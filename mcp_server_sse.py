import uvicorn
import json
from fastapi import FastAPI, Request
from mcp.server import Server
from mcp.server.sse import SseServerTransport
import mcp.types as types
from mcp_server import CapCutMCPServer

# 初始化 FastAPI 应用
app = FastAPI()

# 初始化 CapCut 逻辑服务
capcut_svc = CapCutMCPServer()

# 初始化 MCP Server
mcp_server = Server("capcut-api")

# 初始化 SSE 传输层
sse = SseServerTransport("/messages")


@mcp_server.list_tools()
async def list_tools() -> list[types.Tool]:
    """列出可用工具"""
    return [types.Tool(**t) for t in capcut_svc.get_tools()]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """调用工具"""
    # 复用 CapCutMCPServer 的 call_tool 逻辑
    result = capcut_svc.call_tool(name, arguments)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


@app.get("/sse")
async def handle_sse(request: Request):
    """处理 SSE 连接"""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )


@app.post("/messages")
async def handle_messages(request: Request):
    """处理客户端消息"""
    await sse.handle_post_message(request.scope, request.receive, request._send)


if __name__ == "__main__":
    # 启动服务器，监听 5001 端口
    uvicorn.run(app, host="0.0.0.0", port=5001)
