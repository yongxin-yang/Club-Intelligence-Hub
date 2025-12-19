"""
File: app/mcp_server/backend1_adapter/client.py
Function: 封装对 Backend1 API 的 HTTP 调用
Class/Function:
    Backend1Client: 提供 search_members 和 create_ticket 方法
Call:
    由 app.mcp_server.server 导入使用
"""

import httpx
from typing import List, Dict, Any

BACKEND1_URL = "http://127.0.0.1:8001"

class Backend1Client:
    def __init__(self, base_url: str = BACKEND1_URL):
        self.base_url = base_url

    def search_members(self, keyword: str) -> List[Dict[str, Any]]:
        try:
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/members", params={"keyword": keyword})
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[ERROR] Backend1 search_members failed: {e}")
            return []

    def create_ticket(self, title: str, content: str) -> Dict[str, Any]:
        try:
            with httpx.Client(base_url=self.base_url) as client:
                payload = {"title": title, "content": content}
                response = client.post("/tickets", json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[ERROR] Backend1 create_ticket failed: {e}")
            return {"error": str(e)}

    def list_activities(self) -> List[Dict[str, Any]]:
        try:
            with httpx.Client(base_url=self.base_url) as client:
                response = client.get("/activities")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"[ERROR] Backend1 list_activities failed: {e}")
            return []

# 全局单例
backend1 = Backend1Client()
