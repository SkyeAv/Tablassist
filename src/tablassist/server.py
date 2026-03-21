from fastmcp import FastMCP

MCP: FastMCP = FastMCP(name="tablassist", version="0.1.0")


def run() -> None:
    MCP.run()
