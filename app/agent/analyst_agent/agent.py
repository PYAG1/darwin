from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from .sub_agents.funny_nerd.agent import funny_nerd
from .sub_agents.chat_agent.agent import chat_agent



root_agent = Agent(
    name="analyst_agent",
    model="gemini-2.0-flash",
    description="Manager agent",
    instruction="""
    You are a manager agent that is responsible for overseeing the work of the other agents.

    Always delegate the task to the appropriate agent. Use your best judgement 
    to determine which agent to delegate to.

    You are responsible for delegating tasks to the following agent:
    - chat_agent
    - funny_nerd

  
    """,
    sub_agents=[chat_agent, funny_nerd],

)
