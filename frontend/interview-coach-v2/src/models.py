"""
核心数据模型 (V2 - 简化版)
适应新的对话式流程设计

设计原则：
- 用户看到的是纯聊天界面
- 内部状态由LLM隐式判断
- 追踪引导尝试次数
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class SessionPhase(Enum):
    """
    会话阶段 - 内部使用，用户不可见
    
    这些阶段是LLM内部判断的，不会展示给用户
    """
    WAITING_PROBLEM = "waiting_problem"      # 等待用户提供题目
    WAITING_CODE = "waiting_code"            # 等待用户提交代码
    GUIDING = "guiding"                      # 引导中（代码错误或用户请求帮助）
    FOLLOWUP = "followup"                    # 追问中（代码正确后的3个问题）
    TEACHING = "teaching"                    # 教学中（5次未答对，给出答案和教学）
    COMPLETED = "completed"                  # 本题结束


class UserIntent(Enum):
    """
    用户意图 - LLM识别
    """
    SUBMIT_CODE = "submit_code"              # 提交代码
    ASK_FOR_HELP = "ask_for_help"            # 请求帮助/提示
    ANSWER_QUESTION = "answer_question"      # 回答引导问题
    ASK_QUESTION = "ask_question"            # 提问
    SKIP_PROBLEM = "skip_problem"            # 跳过当前题目
    OTHER = "other"                          # 其他


class CodeEvaluation(Enum):
    """
    代码评估结果
    """
    CORRECT = "correct"                      # 正确
    INCORRECT = "incorrect"                  # 错误
    PARTIAL = "partial"                      # 部分正确
    CANNOT_EVALUATE = "cannot_evaluate"      # 无法评估


@dataclass
class Problem:
    """题目信息"""
    title: str
    description: str
    difficulty: str = "medium"               # easy, medium, hard
    expected_complexity: Optional[str] = None
    test_cases: List[Dict] = field(default_factory=list)
    solution_hints: List[str] = field(default_factory=list)  # 用于LLM引导
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "expected_complexity": self.expected_complexity,
            "test_cases": self.test_cases
        }


@dataclass
class Message:
    """对话消息"""
    role: str                                # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class GuidanceState:
    """
    引导状态追踪
    
    追踪用户在引导过程中的尝试次数
    """
    attempt_count: int = 0                   # 当前尝试次数
    max_attempts: int = 5                    # 最大尝试次数
    current_hint_level: int = 1              # 当前提示强度 (1-3)
    topics_covered: List[str] = field(default_factory=list)  # 已讨论的话题
    
    def increment_attempt(self) -> bool:
        """
        增加尝试次数
        Returns: True if still have attempts left, False if exhausted
        """
        self.attempt_count += 1
        # 自动升级提示强度
        if self.attempt_count >= 3:
            self.current_hint_level = min(3, self.current_hint_level + 1)
        return self.attempt_count < self.max_attempts
    
    def is_exhausted(self) -> bool:
        """是否已用尽尝试次数"""
        return self.attempt_count >= self.max_attempts
    
    def reset(self):
        """重置引导状态"""
        self.attempt_count = 0
        self.current_hint_level = 1
        self.topics_covered = []


@dataclass
class FollowUpState:
    """
    追问状态追踪
    """
    questions_asked: int = 0                 # 已问问题数
    total_questions: int = 3                 # 总共要问的问题数
    questions_history: List[str] = field(default_factory=list)
    
    def add_question(self, question: str):
        """记录已问的问题"""
        self.questions_history.append(question)
        self.questions_asked += 1
    
    def is_complete(self) -> bool:
        """是否完成所有追问"""
        return self.questions_asked >= self.total_questions
    
    def reset(self):
        """重置追问状态"""
        self.questions_asked = 0
        self.questions_history = []


@dataclass
class Session:
    """
    会话状态 - 核心数据结构
    
    管理整个面试对话的状态
    """
    session_id: str
    problem: Optional[Problem] = None
    phase: SessionPhase = SessionPhase.WAITING_PROBLEM
    
    # 对话历史
    messages: List[Message] = field(default_factory=list)
    
    # 用户提交的代码
    user_code: Optional[str] = None
    
    # 引导和追问状态
    guidance_state: GuidanceState = field(default_factory=GuidanceState)
    followup_state: FollowUpState = field(default_factory=FollowUpState)
    
    # 时间戳
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        """添加消息到历史"""
        msg = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(msg)
        self.updated_at = datetime.now()
    
    def get_conversation_history(self, last_n: int = None) -> List[Dict]:
        """
        获取对话历史（用于LLM上下文）
        
        Args:
            last_n: 只获取最近n条，None表示全部
        """
        messages = self.messages[-last_n:] if last_n else self.messages
        return [msg.to_dict() for msg in messages]
    
    def get_context_for_llm(self) -> Dict:
        """
        获取LLM需要的上下文信息
        
        这个上下文会帮助LLM做出正确判断
        """
        return {
            "problem": self.problem.to_dict() if self.problem else None,
            "phase": self.phase.value,
            "user_code": self.user_code,
            "guidance_attempts": self.guidance_state.attempt_count,
            "guidance_remaining": self.guidance_state.max_attempts - self.guidance_state.attempt_count,
            "hint_level": self.guidance_state.current_hint_level,
            "followup_progress": f"{self.followup_state.questions_asked}/{self.followup_state.total_questions}",
            "conversation_history": self.get_conversation_history(last_n=10)
        }
    
    def transition_to(self, new_phase: SessionPhase):
        """状态转换"""
        self.phase = new_phase
        self.updated_at = datetime.now()
    
    def start_guidance(self):
        """开始引导流程"""
        self.guidance_state.reset()
        self.transition_to(SessionPhase.GUIDING)
    
    def start_followup(self):
        """开始追问流程"""
        self.followup_state.reset()
        self.transition_to(SessionPhase.FOLLOWUP)
    
    def start_teaching(self):
        """开始教学流程（用尽尝试后）"""
        self.transition_to(SessionPhase.TEACHING)
    
    def complete(self):
        """完成当前题目"""
        self.transition_to(SessionPhase.COMPLETED)
    
    def reset_for_new_problem(self):
        """重置会话以开始新题目"""
        self.problem = None
        self.user_code = None
        self.guidance_state.reset()
        self.followup_state.reset()
        self.transition_to(SessionPhase.WAITING_PROBLEM)
        # 不清空消息历史，保持对话连续性


@dataclass 
class LLMResponse:
    """
    LLM响应的结构化表示
    """
    # 给用户的回复内容
    reply: str
    
    # 内部判断结果
    detected_intent: Optional[UserIntent] = None
    code_evaluation: Optional[CodeEvaluation] = None
    should_transition: bool = False
    next_phase: Optional[SessionPhase] = None
    
    # 元数据
    reasoning: Optional[str] = None          # LLM的推理过程（调试用）
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "reply": self.reply,
            "detected_intent": self.detected_intent.value if self.detected_intent else None,
            "code_evaluation": self.code_evaluation.value if self.code_evaluation else None,
            "should_transition": self.should_transition,
            "next_phase": self.next_phase.value if self.next_phase else None,
            "reasoning": self.reasoning,
            "confidence": self.confidence
        }


# ==================== 工具函数 ====================

def create_session(session_id: str = None) -> Session:
    """创建新会话"""
    import uuid
    return Session(
        session_id=session_id or str(uuid.uuid4())
    )


def create_problem(
    title: str,
    description: str,
    difficulty: str = "medium",
    expected_complexity: str = None,
    test_cases: List[Dict] = None
) -> Problem:
    """创建题目"""
    return Problem(
        title=title,
        description=description,
        difficulty=difficulty,
        expected_complexity=expected_complexity,
        test_cases=test_cases or []
    )
