"""
测试套件 - V2

测试核心流程：
1. 代码正确 → 追问流程
2. 代码错误 → 引导流程
3. 用户请求帮助 → 引导流程
4. 5次未答对 → 教学流程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Session, SessionPhase, Problem, UserIntent,
    GuidanceState, FollowUpState, create_session
)
from src.coach_engine import CoachEngine
from src.llm_client import MockLLMClient, set_llm_client
from src.prompt_library import PromptLibrary
from src.problem_library import get_problem_library, TWO_SUM


class TestModels:
    """测试数据模型"""
    
    def test_session_creation(self):
        """测试会话创建"""
        session = create_session()
        assert session.session_id is not None
        assert session.phase == SessionPhase.WAITING_PROBLEM
        assert len(session.messages) == 0
        print("✓ test_session_creation")
    
    def test_guidance_state(self):
        """测试引导状态"""
        state = GuidanceState()
        
        # 初始状态
        assert state.attempt_count == 0
        assert state.max_attempts == 5
        assert not state.is_exhausted()
        
        # 增加尝试
        for i in range(4):
            assert state.increment_attempt() == True
            assert not state.is_exhausted()
        
        # 第5次
        assert state.increment_attempt() == False
        assert state.is_exhausted()
        
        # 重置
        state.reset()
        assert state.attempt_count == 0
        print("✓ test_guidance_state")
    
    def test_followup_state(self):
        """测试追问状态"""
        state = FollowUpState()
        
        assert state.questions_asked == 0
        assert not state.is_complete()
        
        # 添加问题
        state.add_question("Q1")
        state.add_question("Q2")
        state.add_question("Q3")
        
        assert state.questions_asked == 3
        assert state.is_complete()
        assert len(state.questions_history) == 3
        print("✓ test_followup_state")
    
    def test_session_messages(self):
        """测试会话消息管理"""
        session = create_session()
        
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi there!")
        
        assert len(session.messages) == 2
        
        history = session.get_conversation_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
        print("✓ test_session_messages")
    
    def test_session_transitions(self):
        """测试状态转换"""
        session = create_session()
        
        # 初始状态
        assert session.phase == SessionPhase.WAITING_PROBLEM
        
        # 开始引导
        session.start_guidance()
        assert session.phase == SessionPhase.GUIDING
        
        # 开始追问
        session.start_followup()
        assert session.phase == SessionPhase.FOLLOWUP
        
        # 完成
        session.complete()
        assert session.phase == SessionPhase.COMPLETED
        print("✓ test_session_transitions")
    
    def run_all(self):
        """运行所有模型测试"""
        print("\n=== 模型测试 ===")
        self.test_session_creation()
        self.test_guidance_state()
        self.test_followup_state()
        self.test_session_messages()
        self.test_session_transitions()
        print("模型测试全部通过！\n")


class TestPromptLibrary:
    """测试Prompt库"""
    
    def __init__(self):
        self.prompts = PromptLibrary()
        self.session = self._create_test_session()
    
    def _create_test_session(self) -> Session:
        """创建测试会话"""
        session = create_session()
        session.problem = TWO_SUM
        session.phase = SessionPhase.WAITING_CODE
        return session
    
    def test_intent_recognition_prompt(self):
        """测试意图识别Prompt"""
        prompt = self.prompts.get_intent_recognition_prompt(
            self.session, 
            "def two_sum(nums, target): pass"
        )
        
        assert "意图" in prompt or "intent" in prompt.lower()
        assert "JSON" in prompt
        print("✓ test_intent_recognition_prompt")
    
    def test_code_evaluation_prompt(self):
        """测试代码评估Prompt"""
        code = """
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
"""
        prompt = self.prompts.get_code_evaluation_prompt(self.session, code)
        
        assert self.session.problem.title in prompt
        assert code.strip()[:50] in prompt
        print("✓ test_code_evaluation_prompt")
    
    def test_guidance_prompt(self):
        """测试引导Prompt"""
        self.session.phase = SessionPhase.GUIDING
        self.session.guidance_state.attempt_count = 2
        
        prompt = self.prompts.get_guidance_prompt(
            self.session,
            "我想用两个循环"
        )
        
        assert "引导" in prompt or "guidance" in prompt.lower()
        assert "两个循环" in prompt
        print("✓ test_guidance_prompt")
    
    def test_followup_prompt(self):
        """测试追问Prompt"""
        self.session.user_code = "def two_sum(nums, target): ..."
        
        prompt = self.prompts.get_followup_prompt(self.session, 1)
        
        assert "追问" in prompt or "followup" in prompt.lower()
        print("✓ test_followup_prompt")
    
    def test_teaching_prompt(self):
        """测试教学Prompt"""
        prompt = self.prompts.get_teaching_prompt(self.session)
        
        assert "答案" in prompt or "解法" in prompt
        print("✓ test_teaching_prompt")
    
    def test_hint_levels(self):
        """测试提示强度"""
        for level in [1, 2, 3]:
            instruction = self.prompts._get_hint_level_instruction(level)
            assert f"Level {level}" in instruction or f"级别" in instruction
        print("✓ test_hint_levels")
    
    def run_all(self):
        """运行所有Prompt测试"""
        print("\n=== Prompt库测试 ===")
        self.test_intent_recognition_prompt()
        self.test_code_evaluation_prompt()
        self.test_guidance_prompt()
        self.test_followup_prompt()
        self.test_teaching_prompt()
        self.test_hint_levels()
        print("Prompt库测试全部通过！\n")


class TestCoachEngine:
    """测试教练引擎"""
    
    def __init__(self):
        # 使用Mock LLM
        self.mock_llm = MockLLMClient()
        set_llm_client(self.mock_llm)
        self.engine = CoachEngine()
    
    def test_session_creation(self):
        """测试会话创建"""
        session = self.engine.create_session()
        
        assert session is not None
        assert session.session_id is not None
        
        # 应该能通过ID获取
        retrieved = self.engine.get_session(session.session_id)
        assert retrieved == session
        print("✓ test_session_creation")
    
    def test_set_problem(self):
        """测试设置题目"""
        session = self.engine.create_session()
        opening = self.engine.set_problem(session.session_id, TWO_SUM)
        
        assert session.problem == TWO_SUM
        assert session.phase == SessionPhase.WAITING_CODE
        assert "两数之和" in opening
        print("✓ test_set_problem")
    
    def test_correct_code_flow(self):
        """测试代码正确的流程"""
        # 设置Mock返回正确评估 - 使用"评估代码"作为key
        self.mock_llm.set_response("评估代码", {
            "evaluation": "correct",
            "reply": "代码正确！",
            "issues": []
        })
        
        session = self.engine.create_session()
        self.engine.set_problem(session.session_id, TWO_SUM)
        
        # 提交代码
        response = self.engine.process_input(
            session.session_id,
            """def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target-num], i]
        seen[num] = i
    return []"""
        )
        
        # 应该进入追问阶段
        assert session.phase == SessionPhase.FOLLOWUP
        print("✓ test_correct_code_flow")
    
    def test_incorrect_code_flow(self):
        """测试代码错误的流程"""
        # 重新创建mock以清除之前的设置
        self.mock_llm = MockLLMClient()
        set_llm_client(self.mock_llm)
        self.engine = CoachEngine()
        
        # 设置Mock返回错误评估
        self.mock_llm.set_response("评估代码", {
            "evaluation": "incorrect",
            "reply": "代码有些问题，让我们想想...",
            "issues": ["边界条件"]
        })
        
        session = self.engine.create_session()
        self.engine.set_problem(session.session_id, TWO_SUM)
        
        # 提交错误代码
        response = self.engine.process_input(
            session.session_id,
            "def two_sum(nums, target): return []"
        )
        
        # 应该进入引导阶段
        assert session.phase == SessionPhase.GUIDING
        print("✓ test_incorrect_code_flow")
    
    def test_help_request_flow(self):
        """测试请求帮助的流程"""
        session = self.engine.create_session()
        self.engine.set_problem(session.session_id, TWO_SUM)
        
        # 请求帮助
        response = self.engine.process_input(
            session.session_id,
            "我不知道怎么做，能给我一些提示吗？"
        )
        
        # 应该进入引导阶段
        assert session.phase == SessionPhase.GUIDING
        assert session.guidance_state.attempt_count == 1
        print("✓ test_help_request_flow")
    
    def test_guidance_exhaustion(self):
        """测试引导次数用尽"""
        session = self.engine.create_session()
        self.engine.set_problem(session.session_id, TWO_SUM)
        
        # 进入引导
        self.engine.process_input(session.session_id, "我不会")
        
        # 模拟5次尝试
        for i in range(5):
            if session.guidance_state.is_exhausted():
                break
            self.engine.process_input(
                session.session_id,
                f"我还是不知道 {i}"
            )
        
        # 应该进入教学阶段
        assert session.phase == SessionPhase.TEACHING
        print("✓ test_guidance_exhaustion")
    
    def test_skip_problem(self):
        """测试跳过题目"""
        session = self.engine.create_session()
        self.engine.set_problem(session.session_id, TWO_SUM)
        
        # 跳过
        response = self.engine.process_input(
            session.session_id,
            "跳过这道题"
        )
        
        # 应该完成并给出答案
        assert session.phase == SessionPhase.COMPLETED
        print("✓ test_skip_problem")
    
    def test_intent_recognition(self):
        """测试意图识别"""
        session = self.engine.create_session()
        session.problem = TWO_SUM
        
        # 测试代码提交意图
        intent, _ = self.engine._recognize_intent(
            session,
            "def two_sum(nums, target): return []"
        )
        assert intent == UserIntent.SUBMIT_CODE
        
        # 测试帮助请求意图
        intent, _ = self.engine._recognize_intent(
            session,
            "给我一些提示"
        )
        assert intent == UserIntent.ASK_FOR_HELP
        
        # 测试跳过意图
        intent, _ = self.engine._recognize_intent(
            session,
            "跳过"
        )
        assert intent == UserIntent.SKIP_PROBLEM
        print("✓ test_intent_recognition")
    
    def run_all(self):
        """运行所有引擎测试"""
        print("\n=== 教练引擎测试 ===")
        self.test_session_creation()
        self.test_set_problem()
        self.test_correct_code_flow()
        self.test_incorrect_code_flow()
        self.test_help_request_flow()
        self.test_guidance_exhaustion()
        self.test_skip_problem()
        self.test_intent_recognition()
        print("教练引擎测试全部通过！\n")


class TestIntegration:
    """集成测试 - 完整对话流程"""
    
    def __init__(self):
        self.mock_llm = MockLLMClient()
        set_llm_client(self.mock_llm)
        self.engine = CoachEngine()
    
    def test_full_correct_flow(self):
        """测试完整的正确代码流程"""
        print("\n--- 测试：完整正确代码流程 ---")
        
        # 创建会话
        session = self.engine.create_session()
        opening = self.engine.set_problem(session.session_id, TWO_SUM)
        print(f"教练: {opening[:100]}...")
        
        # 设置正确评估
        self.mock_llm.set_response("代码评估", {
            "evaluation": "correct",
            "reply": "代码正确！让我问你一个问题：时间复杂度是多少？",
            "issues": []
        })
        
        # 提交正确代码
        response = self.engine.process_input(
            session.session_id,
            "def two_sum(nums, target): seen = {}; ..."
        )
        print(f"教练: {response[:100]}...")
        
        assert session.phase == SessionPhase.FOLLOWUP
        print("✓ 进入追问阶段")
        
        # 回答追问
        for i in range(3):
            response = self.engine.process_input(
                session.session_id,
                f"时间复杂度是O(n)，因为..."
            )
            print(f"教练: {response[:80]}...")
        
        # 应该完成
        assert session.phase == SessionPhase.COMPLETED
        print("✓ test_full_correct_flow")
    
    def test_full_guidance_flow(self):
        """测试完整的引导流程"""
        print("\n--- 测试：完整引导流程 ---")
        
        # 创建会话
        session = self.engine.create_session()
        self.engine.set_problem(session.session_id, TWO_SUM)
        
        # 请求帮助
        response = self.engine.process_input(
            session.session_id,
            "我不知道怎么做"
        )
        print(f"教练: {response[:100]}...")
        
        assert session.phase == SessionPhase.GUIDING
        print(f"✓ 进入引导阶段，尝试次数: {session.guidance_state.attempt_count}")
        
        # 多次尝试
        for i in range(4):
            response = self.engine.process_input(
                session.session_id,
                "我想用两个循环遍历"
            )
            print(f"第{i+2}次尝试，教练: {response[:60]}...")
        
        # 应该进入教学
        assert session.phase == SessionPhase.TEACHING
        print("✓ test_full_guidance_flow")
    
    def test_mid_guidance_correct(self):
        """测试引导中途提交正确代码"""
        print("\n--- 测试：引导中途提交正确代码 ---")
        
        session = self.engine.create_session()
        self.engine.set_problem(session.session_id, TWO_SUM)
        
        # 进入引导
        self.engine.process_input(session.session_id, "给我提示")
        assert session.phase == SessionPhase.GUIDING
        
        # 设置正确评估
        self.mock_llm.set_response("代码评估", {
            "evaluation": "correct",
            "reply": "很好！",
            "issues": []
        })
        
        # 提交正确代码
        response = self.engine.process_input(
            session.session_id,
            "def two_sum(nums, target): return correct_solution()"
        )
        
        # 应该进入追问
        assert session.phase == SessionPhase.FOLLOWUP
        print("✓ test_mid_guidance_correct")
    
    def run_all(self):
        """运行所有集成测试"""
        print("\n=== 集成测试 ===")
        self.test_full_correct_flow()
        self.test_full_guidance_flow()
        self.test_mid_guidance_correct()
        print("\n集成测试全部通过！\n")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("    算法面试教练 V2 - 测试套件")
    print("=" * 60)
    
    # 模型测试
    TestModels().run_all()
    
    # Prompt库测试
    TestPromptLibrary().run_all()
    
    # 引擎测试
    TestCoachEngine().run_all()
    
    # 集成测试
    TestIntegration().run_all()
    
    print("=" * 60)
    print("    ✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
