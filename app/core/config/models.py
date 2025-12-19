from enum import Enum
from typing import Dict, List

class LLMProvider(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    KIMI = "kimi"

class ModelList(Enum):
    # OpenAI
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    
    # DeepSeek
    DEEPSEEK_CHAT = "deepseek-chat"
    DEEPSEEK_CODER = "deepseek-coder"
    
    # Kimi
    MOONSHOT_V1_8K = "moonshot-v1-8k"
    MOONSHOT_V1_32K = "moonshot-v1-32k"

# Mapping provider to their supported models
PROVIDER_MODELS: Dict[LLMProvider, List[str]] = {
    LLMProvider.OPENAI: [
        ModelList.GPT_4O.value,
        ModelList.GPT_4O_MINI.value,
        ModelList.GPT_3_5_TURBO.value
    ],
    LLMProvider.DEEPSEEK: [
        ModelList.DEEPSEEK_CHAT.value,
        ModelList.DEEPSEEK_CODER.value
    ],
    LLMProvider.KIMI: [
        ModelList.MOONSHOT_V1_8K.value,
        ModelList.MOONSHOT_V1_32K.value
    ]
}
