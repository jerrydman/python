import os, shutil
from typing import Dict, List
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters


aws_environment = "dr"
aws_region     = "us-west-2"

def toolset(pkg: str, env: Dict[str, str], add_stdio: bool = True) -> MCPToolset:
    uvx = shutil.which("uvx") or "/opt/homebrew/bin/uvx"
    args = [pkg]
    if add_stdio:
        args += ["--stdio"]         
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=uvx,
                args=args,            
                env=dict(env),       
            )
        )
    )

def env(**overrides) -> Dict[str, str]:
    e = dict(os.environ)        
    e.update({k: v for k, v in overrides.items() if v is not None})
    return e


env_logs    = env(AWS_PROFILE=aws_environment,AWS_REGION=aws_region)
env_tf      = env(AWS_PROFILE=aws_environment,AWS_REGION=aws_region)


CW_PKG = "awslabs.cloudwatch-mcp-server@latest"

tools = [
    toolset(CW_PKG, env_logs),     
    toolset("awslabs.terraform-mcp-server@latest", env_tf),  
]

root_agent = LlmAgent(
    name="AWS_agent",
    description="AWS helper using multiple MCP servers (CloudWatch consolidated package).",
    model="gemini-2.5-flash",
    instruction="Use CloudWatch MCP tools for alarms, metrics, and Logs Insights.",
    tools=tools,
)
