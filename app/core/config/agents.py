from enum import Enum
from typing import Dict, TypedDict

class AgentType(str, Enum):
    DEFAULT = "agent_default"
    FINANCE = "agent_finance"
    ACTIVITY = "agent_activity"

class AgentInfo(TypedDict):
    id: str
    name: str
    description: str
    system_prompt: str

AGENTS: Dict[AgentType, AgentInfo] = {
    AgentType.DEFAULT: {
        "id": AgentType.DEFAULT.value,
        "name": "通用助手",
        "description": "默认的智能助手，可调用所有工具",
        "system_prompt": (
            "You are an AI assistant for the Club AI Hub. "
            "You must use tools to access club systems and data."
        )
    },
    AgentType.FINANCE: {
        "id": AgentType.FINANCE.value,
        "name": "财务助理",
        "description": "专注于财务报销与审批 (Mock)",
        "system_prompt": (
            "You are a Finance Assistant for the Club. "
            "Focus on budget, reimbursement, and financial data. "
            "Always verify amounts and receipt details."
        )
    },
    AgentType.ACTIVITY: {
        "id": AgentType.ACTIVITY.value,
        "name": "活动策划",
        "description": "协助策划社团活动 (Mock)",
        "system_prompt": (
            "You are an Event Planner for the Club. "
            "Help members organize activities, check venues, and manage schedules."
        )
    }
}
