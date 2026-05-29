import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from langchain_core.callbacks import BaseCallbackHandler

# Use the classic path for AgentExecutor and create_tool_calling_agent
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent

import tools

class AgentTracerCallbackHandler(BaseCallbackHandler):
    """
    Custom LangChain Callback Handler to hook into agent actions 
    and bridge tool calls to the Streamlit tracing UI.
    """
    def __init__(self, callback_log=None):
        super().__init__()
        self.callback_log = callback_log
        self.traces = []
        self.step = 0
        self.current_tool_name = None
        self.current_tool_args = None

    def on_llm_start(self, serialized, prompts, **kwargs):
        if self.callback_log:
            self.callback_log("agent_thinking", "Agent reasoning loop running...", {})

    def on_agent_action(self, action, **kwargs):
        self.step += 1
        self.current_tool_name = action.tool
        # LangChain tool inputs can be strings or dicts
        self.current_tool_args = action.tool_input if isinstance(action.tool_input, dict) else {"input": action.tool_input}
        
        if self.callback_log:
            self.callback_log(
                "tool_call_start", 
                f"🤖 Agent decided to run **{self.current_tool_name}** with arguments: `{json.dumps(self.current_tool_args)}`", 
                {"tool": self.current_tool_name, "args": self.current_tool_args}
            )

    def on_tool_end(self, output, **kwargs):
        # Format tool output for reporting
        output_dict = {}
        if isinstance(output, str):
            try:
                output_dict = json.loads(output)
            except Exception:
                output_dict = {"summary": output}
        elif isinstance(output, dict):
            output_dict = output
            
        success = output_dict.get("success", True)
        status_indicator = "✅ Success" if success else "❌ Error"
        summary_text = output_dict.get("summary", output_dict.get("message", str(output)))
        
        if self.callback_log:
            self.callback_log(
                "tool_call_result", 
                f"{status_indicator} from **{self.current_tool_name}**: `{summary_text}`",
                {"tool": self.current_tool_name, "output": output_dict}
            )
            
        self.traces.append({
            "step": self.step,
            "tool": self.current_tool_name,
            "arguments": self.current_tool_args,
            "result": output_dict
        })


def run_travel_agent(user_prompt: str, callback_log=None) -> dict:
    """
    Runs the LangChain Groq GenAI ToolCalling Agent.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "success": False,
            "itinerary": "Error: GROQ_API_KEY is not set in environment or sidebar.",
            "traces": []
        }
    
    # Initialize the LLM via LangChain Groq GenAI
    llm = ChatGroq(
        model="llama-3.1-8b-instant", 
        temperature=0.2,
        api_key=api_key
    )
    
    langchain_tools = [
        StructuredTool.from_function(func=tools.search_flights, name="search_flights", description="Search flights between cities. Returns available options."),
        StructuredTool.from_function(func=tools.recommend_hotels, name="recommend_hotels", description="Search hotels in a city with filters."),
        StructuredTool.from_function(func=tools.discover_places, name="discover_places", description="Discover attractions in a city."),
        StructuredTool.from_function(func=tools.lookup_weather, name="lookup_weather", description="Lookup weather for destination."),
        StructuredTool.from_function(func=tools.estimate_budget, name="estimate_budget", description="Accepts a summary string to finalize total budget calculations.")
    ]
    
    system_instruction = (
    "You are an Elite Travel Specialist AI assistant. You must plan immaculate, personalized itineraries.\n"
    "Follow these execution guidelines:\n"
    "1. Identify the source, all destination cities, dates, and budget criteria. FOR MULTI-CITY TRIPS, plan each leg and destination thoroughly.\n"
    "2. CALL TOOLS systematically: 'search_flights' and 'recommend_hotels' for EACH segment.\n"
    "3. Log all costs and weather daily into the Expense & Weather Log table.\n"
    "4. Output your plan strictly in this Markdown format:\n\n"
    "# ✈️ TRIP PLAN & ITINERARY\n\n"
    "## 📋 TRIP SUMMARY\n"
    "- **Origin**: [Origin City]\n"
    "- **Destinations**: [List all cities]\n"
    "- **Total Duration**: [X] Days\n"
    "- **Dates**: [Dates]\n\n"
    "## 🎫 SELECTED FLIGHT OPTIONS\n"
    "(Repeat this block for EVERY flight leg)\n"
    "- **From**: [Source City] -> **To**: [Destination City]\n"
    "- **Airline & Flight**: [Airline Code]\n"
    "- **Schedule**: [Time] -> [Time]\n"
    "- **Price**: ₹[Price]\n"
    "- **Duration & Speed**: [Duration] (Selected because: [Cheapest/Fastest/Balanced])\n\n"
    "## 🏨 RECOMMENDED HOTELS\n"
    "(Repeat this block for EVERY destination city)\n"
    "- **Hotel Name**: [Name] in [City]\n"
    "- **Address**: [Address]\n"
    "- **Star Rating**: [Rating]/5 ★\n"
    "- **Price**: ₹[Price]/night\n"
    "- **Selected Amenities**: [Amenities]\n"
    "- **Why selected**: [Reasoning based on rating/price]\n\n"
    "## 📅 DAY-BY-DAY EXPENSE & WEATHER LOG\n"
    "| Date | City | Activity Summary | Flight Cost | Hotel Cost | Weather (Min/Max °C) |\n"
    "| --- | --- | --- | --- | --- | --- |\n"
    "| [Date] | [City] | [Description] | ₹[Cost] | ₹[Cost] | [Min]/[Max] |\n\n"
    "## 💰 BUDGET BREAKDOWN & ESTIMATION\n"
    "| Expense Category | Total Cost |\n"
    "| --- | --- |\n"
    "| **Total Flights** | ₹[Sum of all flights] |\n"
    "| **Total Lodging** | ₹[Sum of all hotels] |\n"
    "| **GRAND TOTAL** | **₹[Grand Total]** |\n\n"
    "## 🧠 PLANNING & REASONING SUMMARY\n"
    "[Explain how this itinerary maximizes value, logistics, and weather optimization.]"
)
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    agent_runnable = create_tool_calling_agent(
        llm=llm,
        tools=langchain_tools,
        prompt=prompt_template
    )
    
    agent_executor = AgentExecutor(
        agent=agent_runnable,
        tools=langchain_tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True
    )
    
    tracer = AgentTracerCallbackHandler(callback_log=callback_log)
    
    try:
        if callback_log:
            callback_log("agent_thinking", "Initializing LangChain Specialist Agent...", {})
            
        response = agent_executor.invoke(
            {"input": user_prompt},
            config={"callbacks": [tracer]}
        )
        
        if callback_log:
            callback_log("agent_complete", "✨ Agent planning complete!", {})
            
        return {
            "success": True,
            "itinerary": response["output"],
            "traces": tracer.traces
        }
    except Exception as err:
        return {
            "success": False,
            "itinerary": f"Error running agent: {str(err)}",
            "traces": tracer.traces
        }
