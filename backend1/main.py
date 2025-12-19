"""
File: backend1/main.py
Function: 模拟社团业务系统后端 API (Backend1)
Class/Function:
    FastAPI app: 提供成员查询与工单创建接口
Call:
    由 app.mcp_server (Adapter) 调用
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Backend1 System", description="Simulated Club Management System")

# 模拟数据库
FAKE_MEMBERS = [
    {"id": "1", "name": "Alice", "role": "President", "email": "alice@club.com"},
    {"id": "2", "name": "Bob", "role": "Member", "email": "bob@club.com"},
    {"id": "3", "name": "Charlie", "role": "Vice President", "email": "charlie@club.com"},
]

FAKE_TICKETS = []

FAKE_ACTIVITIES = [
    {"id": "1", "name": "Annual Party", "time": "2025-12-31 20:00", "location": "Hall A"},
    {"id": "2", "name": "Tech Talk", "time": "2025-12-25 15:00", "location": "Room 101"},
]

class TicketCreate(BaseModel):
    title: str
    content: str

class Ticket(BaseModel):
    id: str
    title: str
    content: str
    status: str


@app.get("/members", response_model=List[Dict[str, str]])
def get_members(keyword: Optional[str] = None):
    """根据关键词模糊查询成员"""
    if not keyword:
        return FAKE_MEMBERS
    
    return [
        m for m in FAKE_MEMBERS 
        if keyword.lower() in m["name"].lower()
    ]

@app.post("/tickets", response_model=Ticket)
def create_ticket(ticket: TicketCreate):
    """创建新工单"""
    ticket_id = str(len(FAKE_TICKETS) + 1)
    new_ticket = {
        "id": ticket_id,
        "title": ticket.title,
        "content": ticket.content,
        "status": "created"
    }
    FAKE_TICKETS.append(new_ticket)
    return new_ticket

@app.get("/tickets", response_model=List[Dict[str, str]])
def list_tickets():
    """列出所有工单"""
    return FAKE_TICKETS

@app.get("/activities", response_model=List[Dict[str, str]])
def list_activities():
    """列出所有活动"""
    return FAKE_ACTIVITIES

if __name__ == "__main__":
    # 运行在 8001 端口, 避免与 Gateway (8000) 和 MCP Server (3333) 冲突
    uvicorn.run(app, host="127.0.0.1", port=8001)
