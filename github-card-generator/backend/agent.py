from google.adk import Agent
from google.adk.tools import McpToolset

from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp.client.stdio import StdioServerParameters


mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["mcp_server.py"]
        )
    )
)

github_card_agent = Agent(
    name="github_card_agent",
    model="gemini-2.5-flash",
    instruction=
"You are a GitHub profile analyst and dev card generator. When a user gives you a GitHub username, you ALWAYS follow this exact sequence: first call scrape_github, then analyze_profile with the result, then generate_card_html with all three inputs, then save_card. Never skip steps. Be enthusiastic about developers' work. If the profile is private or doesn't exist, say so clearly.",
    tools=[mcp_toolset]
)