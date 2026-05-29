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
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "success": False,
            "itinerary": "Error: GROQ_API_KEY or GEMINI_API_KEY is not set in environment or sidebar.",
            "traces": []
        }
    
    # Initialize the LLM via LangChain Groq GenAI (using robust gemini-3.5-flash)
    llm = ChatGroq(
    model="llama-3.1-8b-instant", # Groq supports high-speed Llama 3 models
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY") # You'll need to set this secret in Colab

    )
    
    # Bind Python tools seamlessly into LangChain Structured Tools
    # This matches the local dataset loaders and live Open-Meteo API
    langchain_tools = [
        StructuredTool.from_function(
            func=tools.search_flights,
            name="search_flights",
            description="Search available flights from a source city to a destination city. Returns available options, cheapest and fastest options."
        ),
        StructuredTool.from_function(
            func=tools.recommend_hotels,
            name="recommend_hotels",
            description="Search and recommend hotels in a given destination city with optional min_rating (e.g. 4.0) and max_price filters."
        ),
        StructuredTool.from_function(
            func=tools.discover_places,
            name="discover_places",
            description="Discover recommended points of interest, tourist spots and attractions in a city based on type and rating."
        ),
        StructuredTool.from_function(
            func=tools.lookup_weather,
            name="lookup_weather",
            description="Lookup the weather forecast for the destination city during specified dates in YYYY-MM-DD format."
        ),
        StructuredTool.from_function(
            func=tools.estimate_budget,
            name="estimate_budget",
            description="Utility tool to calculate and break down the total budget sum based on flights, hotels, daily expenses, and duration."
        )
    ]
    
    system_instruction = (
        "You are an Elite Travel Specialist AI assistant designed to plan immaculate, personalized travel itineraries.\n"
        "Your goal is to satisfy the user's travel requests by calling the appropriate planning tools iteratively to gather reliable intelligence, analyze alternative choices, and construct a robust plan.\n\n"
        "Follow these execution guidelines:\n"
        "1. Identify the source, destination, travel dates (or duration), and budget criteria in the user request.\n"
        "2. CALL TOOLS systematically to check flights, hotels, weather forecast, and attraction options.\n"
        "3. Once you obtain flights and hotels, use the estimate_budget tool to calculate the exact totals.\n"
        "4. Create a comprehensive, day-by-day itinerary (typically 3-7 days based on their request) specifying daily activities, sightseeing recommendations, meal stops, and coordinates.\n"
        "5. Output your final travel plan strictly in the following beautifully structured Markdown format:\n\n"
        "# ✈️ TRIP PLAN & ITINERARY: [Destination]\n\n"
        "## 📋 TRIP SUMMARY\n"
        "- **Origin**: [Origin City]\n"
        "- **Destination**: [Destination City]\n"
        "- **Duration**: [X] Days\n"
        "- **Dates**: [Dates, or 'Flexible']\n\n"
        "## 🎫 SELECTED FLIGHT OPTION\n"
        "- **Airline & Flight**: [e.g. Air France AF015]\n"
        "- **Schedule**: [Departure Time] -> [Arrival Time]\n"
        "- **Price**: ₹[Price] Round Trip\n"
        "- **Duration & Speed**: [Duration] (Selected because [Cheapest/Fastest/Balanced])\n\n"
        "## 🏨 RECOMMENDED HOTEL\n"
        "- **Hotel Name**: [Hotel Name]\n"
        "- **Address**: [Address]\n"
        "- **Star Rating**: [Rating]/5 ★\n"
        "- **Price**: ₹[Price]/night\n"
        "- **Selected Amenities**: [Free Wi-Fi, Pool, etc.]\n"
        "- **Why selected**: [Reasoning based on ratings/price]\n\n"
        "## 📅 DAY-BY-DAY ITINERARY ([X] Days)\n"
        "### Day 1: [Catchy Day Title]\n"
        "- **Weather**: [Temperature Range, Weather Condition]\n"
        "- **Morning**: [Attraction/Museum from tools + description]\n"
        "- **Afternoon**: [Activity, food recommendations]\n"
        "- **Evening**: [Relaxing stroll, dinner neighborhood recommendation]\n\n"
        "[Repeat for each requested day...]\n\n"
        "## ☀️ WEATHER FORECAST SUMMARY\n"
        "[Provide forecast details for the travel days / period, helping them pack appropriate clothes, warnings, etc.]\n\n"
        "## 💰 BUDGET BREAKDOWN & ESTIMATION\n"
        "| Expense Category | Unit / Daily cost | Total Cost | Details |\n"
        "| --- | --- | --- | --- |\n"
        "| **Flights** | - | ₹[Flight Total] | Round trip, Selected flight |\n"
        "| **Lodging** | ₹[Price]/night | ₹[Hotel Total] | [X] nights total |\n"
        "| **GRAND TOTAL** | | **₹[Grand Total]** | **All Calculated Costs** |\n\n"
        "## 🧠 PLANNING & REASONING SUMMARY\n"
        "[Brief paragraph explaining how this trip maximizes value, how activities are logistically close, and weather optimization advice.]"
    )
    
    # Create structural Agent Prompt compatible with LangChain tool calling agents
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # Initialize Groq GenAI Tools Agent runnable
    agent_runnable = create_tool_calling_agent(
        llm=llm,
        tools=langchain_tools,
        prompt=prompt_template
    )
    
    # Create Agent Executor to manage iterative ReAct feedback loop
    agent_executor = AgentExecutor(
        agent=agent_runnable,
        tools=langchain_tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True
    )
    
    # Attach our custom callback tracer
    tracer = AgentTracerCallbackHandler(callback_log=callback_log)
    
    try:
        if callback_log:
            callback_log("agent_thinking", "Initializing LangChain Specialist Agent...", {})
            
        response = agent_executor.invoke(
            {"input": user_prompt},
            config={"callbacks": [tracer]}
        )
        
        if callback_log:
            callback_log("agent_complete", "✨ Agent planning complete! Constructing final response...", {})
            
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

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    
    api_to_test = os.getenv("Groq_API_Key") or os.getenv("GEMINI_API_KEY")
    if not api_to_test:
        print("Please set your GROQ_API_KEY (or GROQ_API_KEY) in .env to run this standalone script.")
    else:
        print("Running LangChain trip travel agent simulation with GROQ GenAI...")
        
        def cli_logger(log_type, message, metadata):
            print(f"[{log_type.upper()}] {message}")
            
        prompt = "I want an ultra optimized 3-day trip from New York to Paris starting June 10th. Cheaper is better."
        result = run_travel_agent(prompt, callback_log=cli_logger)
        print("\n=== FINAL ITINERARY ===")
        print(result["itinerary"])
