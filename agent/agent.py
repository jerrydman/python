import os, shutil
from typing import Dict, List
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

def _stdio_toolset(pkg: str, env: Dict[str, str], add_stdio: bool = True) -> MCPToolset:
    uvx = shutil.which("uvx") or "/opt/homebrew/bin/uvx"
    args = [pkg]
    if add_stdio:
        args += ["--stdio"]          # safe; avoids any port binding
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=uvx,
                args=args,            # ONE package per MCP server
                env=dict(env),        # fresh copy: isolate env per server
            )
        )
    )

def _env(**overrides) -> Dict[str, str]:
    e = dict(os.environ)              # inherit PATH/PROXY/SSL/etc.
    e.update({k: v for k, v in overrides.items() if v is not None})
    e.setdefault("FASTMCP_LOG_LEVEL", "INFO")
    return e


env_logs    = _env(AWS_PROFILE="dr",AWS_REGION="us-west-2")
env_tf      = _env(AWS_PROFILE="dr",AWS_REGION="us-west-2")

# NOTE: use the SAME PACKAGE for both:
CW_PKG = "awslabs.cloudwatch-mcp-server@latest"

tools = [
    _stdio_toolset(CW_PKG, env_logs),      # logs, same package but different env (staging/us-east-1)
    _stdio_toolset("awslabs.terraform-mcp-server@latest", env_tf),  # optional third
]

root_agent = LlmAgent(
    name="AWS_agent",
    description="AWS helper using multiple MCP servers (CloudWatch consolidated package).",
    model="gemini-2.5-flash",
    instruction="Use CloudWatch MCP tools for alarms, metrics, and Logs Insights.",
    tools=tools,
)
