"""
配置管理

支持：
- 环境变量
- 配置文件
- 默认值
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """应用配置"""
    
    # LLM设置
    llm_provider: str = "mock"  # "mock", "openai", "anthropic"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1500
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # 教学设置
    max_guidance_attempts: int = 5
    followup_questions_count: int = 3
    
    # 日志
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "mock"),
            llm_model=os.getenv("LLM_MODEL", "gpt-4"),
            llm_temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            llm_max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1500")),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_guidance_attempts=int(os.getenv("MAX_GUIDANCE_ATTEMPTS", "5")),
            followup_questions_count=int(os.getenv("FOLLOWUP_QUESTIONS_COUNT", "3")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE")
        )


# 默认配置
DEFAULT_CONFIG = Config()


def get_config() -> Config:
    """获取配置"""
    return Config.from_env()
