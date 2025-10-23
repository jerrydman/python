import os, shutil
from typing import Dict, List
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters


aws_environment = "dr"
aws_region     = "us-west-2"

def toolset(pkg: str, env: Dict[str, str]) -> MCPToolset:
    uvx = shutil.which("uvx") or "/opt/homebrew/bin/uvx"
    args = [pkg]
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=uvx,
                args=args,            
                env=dict(env),       
            )
        )
    )

tools = [
    toolset("awslabs.cloudwatch-mcp-server@latest"),     
    toolset("awslabs.terraform-mcp-server@latest"),  
]

root_agent = LlmAgent(
    name="AWS_agent",
    model="gemini-2.5-flash",
    tools=tools,
)