"""
File: app/mcp_server/server.py
Function: 使用 FastMCP 定义社团系统示例工具并启动 MCP Server
Class/Function:
    search_members: 按姓名关键字查询成员
    create_ticket: 创建示例工单
    description: 提供社团系统描述资源
Call:
    由独立进程运行本文件启动 MCP Server, Gateway 通过 HTTP 访问
"""

from typing import Dict, List

from fastmcp import FastMCP


mcp = FastMCP("club-ai-hub")


FAKE_MEMBERS: List[Dict[str, str]] = [
    {"id": "1", "name": "Alice", "role": "President"},
    {"id": "2", "name": "Bob", "role": "Member"},
]


FAKE_TICKETS: List[Dict[str, str]] = []


@mcp.tool()
def search_members(keyword: str) -> List[Dict[str, str]]:
    return [
        member
        for member in FAKE_MEMBERS
        if keyword.lower() in member["name"].lower()
    ]


@mcp.tool()
def create_ticket(title: str, content: str) -> Dict[str, str]:
    ticket_id = str(len(FAKE_TICKETS) + 1)
    ticket = {
        "id": ticket_id,
        "title": title,
        "content": content,
        "status": "created",
    }
    FAKE_TICKETS.append(ticket)
    return ticket


@mcp.resource("club://description")
def description() -> str:
    return (
        "This system manages a student club. "
        "You can search members and create workflow tickets."
    )


if __name__ == "__main__":
    mcp.run(host="127.0.0.1", port=3333)


