"""
File: app/core/llm.py
Function: 统一管理与外部 LLM 服务的配置和客户端创建, 支持多提供方
Class/Function:
    get_llm_provider: 从环境变量读取当前使用的 LLM 提供方
    get_llm_client_and_model: 基于提供方返回 OpenAI 客户端与模型名称
Call:
    由 app.gateway.api 调用以获取统一的 LLM 客户端
"""

import json
import os
from pathlib import Path
from typing import Dict, Tuple

from openai import OpenAI


_LOCAL_KEYS: Dict[str, str] | None = None


def get_llm_provider() -> str:
    provider = os.environ.get("LLM_PROVIDER", "openai")
    return provider.lower()


def _load_local_keys() -> Dict[str, str]:
    global _LOCAL_KEYS
    if _LOCAL_KEYS is not None:
        return _LOCAL_KEYS

    path_str = os.environ.get("LLM_KEY_FILE", "config/keys.local.json")
    path = Path(path_str)
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        data = json.loads(text)
        if isinstance(data, dict):
            _LOCAL_KEYS = {str(k): str(v) for k, v in data.items()}
        else:
            _LOCAL_KEYS = {}
    else:
        _LOCAL_KEYS = {}
    return _LOCAL_KEYS


def _get_config(name: str) -> str | None:
    value = os.environ.get(name)
    if value is not None:
        return value
    # Force reload keys if not found to ensure latest config is used
    if _LOCAL_KEYS is None or name not in _LOCAL_KEYS:
        _load_local_keys()
    return _LOCAL_KEYS.get(name) if _LOCAL_KEYS else None


def get_llm_client_and_model() -> Tuple[OpenAI, str]:
    provider = get_llm_provider()

    if provider == "openai":
        api_key = _get_config("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY 未配置")
        model = _get_config("OPENAI_MODEL") or "gpt-4o-mini"
        client = OpenAI(api_key=api_key)
        return client, model

    if provider == "deepseek":
        api_key = _get_config("DEEPSEEK_API_KEY")
        base_url = _get_config("DEEPSEEK_BASE_URL")
        if not api_key or not base_url:
            raise RuntimeError("DEEPSEEK_API_KEY 或 DEEPSEEK_BASE_URL 未配置")
        model = _get_config("DEEPSEEK_MODEL") or "deepseek-chat"
        client = OpenAI(api_key=api_key, base_url=base_url)
        return client, model

    if provider == "kimi":
        api_key = _get_config("KIMI_API_KEY")
        base_url = _get_config("KIMI_BASE_URL")
        if not api_key or not base_url:
            raise RuntimeError("KIMI_API_KEY 或 KIMI_BASE_URL 未配置")
        model = _get_config("KIMI_MODEL") or "kimi-chat"
        client = OpenAI(api_key=api_key, base_url=base_url)
        return client, model

    raise RuntimeError(f"不支持的 LLM_PROVIDER: {provider}")
