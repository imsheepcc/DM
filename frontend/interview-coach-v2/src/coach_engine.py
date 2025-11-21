"""
教练引擎 (Coach Engine) - V2

核心控制器，处理所有对话逻辑

流程设计：
1. 用户提交代码后：
   - 正确 → 追问3个问题
   - 错误 → 开始引导
   - 用户请求帮助 → 直接进入引导

2. 引导过程：
   - 动态响应，不重复问题
   - 最多5次尝试
   - 5次后给出答案和教学

3. 所有回复由LLM动态生成
"""

import logging
from typing import Dict, Optional, Tuple
from src.models import (
    Session, SessionPhase, Problem, UserIntent, 
    CodeEvaluation, LLMResponse, create_session
)
from src.prompt_library import PromptLibrary, get_prompt_library
from src.llm_client import BaseLLMClient, get_llm_client

logger = logging.getLogger(__name__)


class CoachEngine:
    """
    教练引擎
    
    核心职责：
    1. 管理会话状态
    2. 协调LLM调用
    3. 实现教学流程
    """
    
    def __init__(
        self, 
        llm_client: BaseLLMClient = None,
        prompt_library: PromptLibrary = None
    ):
        self.llm = llm_client or get_llm_client()
        self.prompts = prompt_library or get_prompt_library()
        self.sessions: Dict[str, Session] = {}
    
    # ==================== 会话管理 ====================
    
    def create_session(self, session_id: str = None) -> Session:
        """创建新会话"""
        session = create_session(session_id)
        self.sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    def set_problem(self, session_id: str, problem: Problem) -> str:
        """
        设置当前题目
        
        Returns:
            开场白
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.problem = problem
        session.transition_to(SessionPhase.WAITING_CODE)
        
        # 生成开场白
        opening = self._generate_opening(session)
        session.add_message("assistant", opening)
        
        return opening
    
    def _generate_opening(self, session: Session) -> str:
        """生成题目开场白"""
        problem = session.problem
        return f"""好的，让我们来看这道题：

**{problem.title}**

{problem.description}

你可以先想一想，然后把你的代码或思路告诉我。如果需要提示，随时可以问我！"""
    
    # ==================== 主处理流程 ====================
    
    def process_input(self, session_id: str, user_input: str) -> str:
        """
        处理用户输入 - 主入口
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            
        Returns:
            教练的回复
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # 记录用户输入
        session.add_message("user", user_input)
        
        # 根据当前阶段处理
        phase = session.phase
        
        if phase == SessionPhase.WAITING_PROBLEM:
            reply = self._handle_waiting_problem(session, user_input)
        
        elif phase == SessionPhase.WAITING_CODE:
            reply = self._handle_waiting_code(session, user_input)
        
        elif phase == SessionPhase.GUIDING:
            reply = self._handle_guiding(session, user_input)
        
        elif phase == SessionPhase.FOLLOWUP:
            reply = self._handle_followup(session, user_input)
        
        elif phase == SessionPhase.TEACHING:
            reply = self._handle_teaching(session, user_input)
        
        elif phase == SessionPhase.COMPLETED:
            reply = self._handle_completed(session, user_input)
        
        else:
            reply = "抱歉，出现了一些问题。让我们重新开始。"
            session.reset_for_new_problem()
        
        # 记录回复
        session.add_message("assistant", reply)
        
        return reply
    
    # ==================== 各阶段处理器 ====================
    
    def _handle_waiting_problem(self, session: Session, user_input: str) -> str:
        """处理等待题目阶段"""
        # 这个阶段一般不会到达，因为题目由系统设置
        return "请先选择一道题目开始练习。"
    
    def _handle_waiting_code(self, session: Session, user_input: str) -> str:
        """
        处理等待代码阶段
        
        三种可能：
        1. 用户提交代码
        2. 用户请求帮助
        3. 用户问问题
        """
        # 首先识别用户意图
        intent, intent_reply = self._recognize_intent(session, user_input)
        
        if intent == UserIntent.SUBMIT_CODE:
            # 提取并评估代码
            return self._evaluate_and_respond(session, user_input)
        
        elif intent == UserIntent.ASK_FOR_HELP:
            # 用户请求帮助，直接进入引导
            session.start_guidance()
            return self._handle_help_request(session, user_input)
        
        elif intent == UserIntent.SKIP_PROBLEM:
            # 用户要跳过
            return self._handle_skip(session)
        
        else:
            # 其他情况，返回意图识别生成的回复
            return intent_reply
    
    def _handle_guiding(self, session: Session, user_input: str) -> str:
        """
        处理引导阶段
        
        核心逻辑：
        1. 理解用户回答
        2. 判断是否正确
        3. 如果正确 → 进入追问
        4. 如果错误 → 继续引导或结束
        """
        # 检查是否用尽尝试
        if session.guidance_state.is_exhausted():
            session.start_teaching()
            return self._generate_teaching(session)
        
        # 检查用户是否想提交新代码
        intent, _ = self._recognize_intent(session, user_input)
        
        if intent == UserIntent.SUBMIT_CODE:
            # 用户提交了新代码，重新评估
            return self._evaluate_and_respond(session, user_input)
        
        if intent == UserIntent.SKIP_PROBLEM:
            return self._handle_skip(session)
        
        # 进行引导对话
        prompt = self.prompts.get_guidance_prompt(session, user_input)
        response = self.llm.call_json(prompt)
        
        reply = response.get("reply", "让我们换个角度想想...")
        on_track = response.get("user_on_right_track", False)
        
        # 增加尝试次数
        has_attempts = session.guidance_state.increment_attempt()
        
        if on_track:
            # 用户在正确方向上，鼓励他们继续
            # 但不直接转换到追问，等用户提交正确代码
            pass
        elif not has_attempts:
            # 用尽尝试，进入教学
            session.start_teaching()
            return self._generate_teaching(session)
        
        return reply
    
    def _handle_followup(self, session: Session, user_input: str) -> str:
        """
        处理追问阶段
        
        评估用户对追问的回答，然后继续下一个追问或结束
        """
        followup_state = session.followup_state
        current_q_num = followup_state.questions_asked
        
        if followup_state.is_complete():
            # 已完成所有追问
            session.complete()
            return self._generate_completion(session)
        
        # 获取上一个追问问题（如果有）
        last_question = followup_state.questions_history[-1] if followup_state.questions_history else ""
        
        if current_q_num == 0:
            # 还没开始追问，生成第一个问题
            return self._generate_followup_question(session)
        
        # 评估用户的回答
        prompt = self.prompts.get_followup_evaluation_prompt(
            session, 
            last_question,
            user_input,
            current_q_num
        )
        response = self.llm.call_json(prompt)
        
        reply = response.get("reply", "")
        
        # 检查是否还有下一个追问
        if current_q_num < followup_state.total_questions:
            next_q = response.get("next_question", "")
            if next_q:
                followup_state.add_question(next_q)
        
        # 检查是否完成
        if followup_state.is_complete():
            session.complete()
            if "恭喜" not in reply and "完成" not in reply:
                reply += "\n\n太棒了！你已经完成了这道题的所有挑战。做得很好！"
        
        return reply
    
    def _handle_teaching(self, session: Session, user_input: str) -> str:
        """
        处理教学阶段
        
        这个阶段在给出答案后，用户可能还有问题
        """
        # 用户可能有后续问题
        return self._answer_post_teaching_question(session, user_input)
    
    def _handle_completed(self, session: Session, user_input: str) -> str:
        """处理已完成阶段"""
        return "这道题我们已经讨论完了。你想继续练习下一道题吗？"
    
    # ==================== 辅助方法 ====================
    
    def _recognize_intent(self, session: Session, user_input: str) -> Tuple[UserIntent, str]:
        """
        识别用户意图
        
        Returns:
            (意图, LLM生成的回复)
        """
        # 快速规则判断
        input_lower = user_input.lower().strip()
        
        # 跳过关键词
        skip_keywords = ["跳过", "换题", "skip", "next", "下一题"]
        if any(kw in input_lower for kw in skip_keywords):
            return UserIntent.SKIP_PROBLEM, ""
        
        # 帮助关键词
        help_keywords = ["帮助", "提示", "hint", "help", "不会", "不知道", "给我提示", "怎么做"]
        if any(kw in input_lower for kw in help_keywords):
            return UserIntent.ASK_FOR_HELP, ""
        
        # 代码特征检测
        code_indicators = ["def ", "function", "class ", "for ", "while ", "if ", "return", "=>", "```"]
        if any(ind in user_input for ind in code_indicators):
            return UserIntent.SUBMIT_CODE, ""
        
        # 使用LLM识别
        prompt = self.prompts.get_intent_recognition_prompt(session, user_input)
        response = self.llm.call_json(prompt)
        
        intent_str = response.get("intent", "other")
        reply = response.get("reply", "")
        
        try:
            intent = UserIntent(intent_str)
        except ValueError:
            intent = UserIntent.OTHER
        
        return intent, reply
    
    def _evaluate_and_respond(self, session: Session, user_input: str) -> str:
        """
        评估代码并生成响应
        
        核心分支：
        - 正确 → 开始追问
        - 错误 → 开始引导
        """
        # 保存用户代码
        session.user_code = user_input
        
        # 调用LLM评估
        prompt = self.prompts.get_code_evaluation_prompt(session, user_input)
        response = self.llm.call_json(prompt)
        
        evaluation = response.get("evaluation", "incorrect")
        reply = response.get("reply", "")
        
        if evaluation == "correct":
            # 代码正确，开始追问
            session.start_followup()
            # 生成第一个追问
            first_followup = self._generate_followup_question(session)
            return f"{reply}\n\n{first_followup}" if reply else first_followup
        
        else:
            # 代码有问题，开始引导
            session.start_guidance()
            return reply
    
    def _generate_followup_question(self, session: Session) -> str:
        """生成追问问题"""
        q_num = session.followup_state.questions_asked + 1
        
        prompt = self.prompts.get_followup_prompt(session, q_num)
        response = self.llm.call_json(prompt)
        
        question = response.get("question", "你能解释一下你的算法的时间复杂度吗？")
        session.followup_state.add_question(question)
        
        return question
    
    def _generate_teaching(self, session: Session) -> str:
        """生成教学内容（5次尝试后）"""
        prompt = self.prompts.get_teaching_prompt(session)
        response = self.llm.call(prompt)  # 教学内容不需要JSON格式
        return response
    
    def _generate_completion(self, session: Session) -> str:
        """生成完成总结"""
        return """🎉 太棒了！你已经完成了这道题！

**你的表现：**
- 代码正确
- 完成了所有追问

继续保持！准备好下一道题了吗？"""
    
    def _handle_help_request(self, session: Session, user_input: str) -> str:
        """处理用户的帮助请求"""
        prompt = self.prompts.get_help_request_prompt(session, user_input)
        response = self.llm.call_json(prompt)
        
        # 增加尝试次数
        session.guidance_state.increment_attempt()
        
        return response.get("reply", "让我们一步步来。首先，你对这道题的第一反应是什么？")
    
    def _handle_skip(self, session: Session) -> str:
        """处理跳过请求"""
        # 先给出简短的答案提示
        session.start_teaching()
        teaching = self._generate_teaching(session)
        
        session.complete()
        
        return f"没问题，让我先给你讲解一下这道题：\n\n{teaching}\n\n准备好下一道题了吗？"
    
    def _answer_post_teaching_question(self, session: Session, user_input: str) -> str:
        """回答教学后的问题"""
        # 使用通用的对话能力回答
        prompt = f"""用户刚刚学习了一道算法题，现在有后续问题：

题目：{session.problem.title}
用户问题：{user_input}

请简洁地回答用户的问题。"""
        
        return self.llm.call(prompt)


# ==================== 便捷函数 ====================

_coach_engine: Optional[CoachEngine] = None

def get_coach_engine() -> CoachEngine:
    """获取全局教练引擎"""
    global _coach_engine
    if _coach_engine is None:
        _coach_engine = CoachEngine()
    return _coach_engine

def set_coach_engine(engine: CoachEngine):
    """设置全局教练引擎"""
    global _coach_engine
    _coach_engine = engine
