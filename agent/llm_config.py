# -*- coding: utf-8 -*-
"""
LLM 模型配置模块

提供简化的 LLM 配置管理
"""

import os
from typing import Optional, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# 从配置或环境变量获取（火山引擎 Ark API）
LLM_API_KEY = os.getenv("ARK_API_KEY", "3eb8e543-8cdc-48e9-b237-a0359f4cdcc6")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
LLM_MODEL = os.getenv("LLM_MODEL", "doubao-seed-1-8-251228")


@dataclass
class LLMConfig:
    """
    LLM 模型配置类
    """
    provider: str = "custom"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = 60000
    streaming: bool = False
    extra_params: dict = field(default_factory=dict)
    
    def get_model_name(self) -> str:
        return self.model or LLM_MODEL
    
    def create_llm(self) -> Any:
        """创建 LLM 实例"""
        from langchain_openai import ChatOpenAI
        
        model_name = self.get_model_name()
        base_url = self.base_url or LLM_BASE_URL
        api_key = self.api_key or LLM_API_KEY
        
        params = {
            "model": model_name,
            "base_url": base_url,
            "api_key": api_key,
            "temperature": self.temperature,
            "streaming": self.streaming,
            **self.extra_params,
        }
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        return ChatOpenAI(**params)


# 全局配置实例
_default_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """获取全局 LLM 配置"""
    global _default_config
    if _default_config is None:
        _default_config = LLMConfig(
            model=LLM_MODEL,
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
        )
    return _default_config


def set_llm_config(config: LLMConfig) -> None:
    """设置全局 LLM 配置"""
    global _default_config
    _default_config = config


def create_llm(config: Optional[LLMConfig] = None) -> Any:
    """创建 LLM 实例"""
    if config is None:
        config = get_llm_config()
    return config.create_llm()


__all__ = [
    "LLMConfig",
    "get_llm_config",
    "set_llm_config",
    "create_llm",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
]
