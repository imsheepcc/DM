"""
算法面试教练 - 主应用

使用方式：
    python -m src.main                 # 启动CLI交互（Mock模式）
    python -m src.main --provider qwen # 使用通义千问
    python -m src.main --problem "两数之和"  # 指定题目
    python -m src.main --random        # 随机题目
    
环境变量：
    DASHSCOPE_API_KEY 或 QWEN_API_KEY  # 通义千问API密钥
    OPENAI_API_KEY                      # OpenAI API密钥
    ANTHROPIC_API_KEY                   # Anthropic API密钥
"""

import argparse
import sys
import os
from typing import Optional

from src.models import Session
from src.coach_engine import CoachEngine, get_coach_engine
from src.problem_library import get_problem_library, Problem
from src.llm_client import (
    create_llm_client, 
    set_llm_client,
    MockLLMClient,
    LLMConfig
)


class InterviewCoachApp:
    """
    面试教练应用
    
    提供CLI交互界面
    """
    
    def __init__(
        self, 
        provider: str = "mock", 
        api_key: str = None,
        model: str = None
    ):
        """
        Args:
            provider: LLM提供商 ("mock", "qwen", "openai", "anthropic")
            api_key: API密钥（可选，也可通过环境变量设置）
            model: 模型名称（可选）
        """
        # 配置LLM
        if provider == "mock":
            set_llm_client(MockLLMClient())
            print("✓ 使用Mock LLM（开发模式）")
        else:
            try:
                config = self._build_llm_config(provider, api_key, model)
                client = create_llm_client(provider, config)
                set_llm_client(client)
                print(f"✓ 使用 {provider} LLM (模型: {config.model})")
            except Exception as e:
                print(f"⚠ 无法连接 {provider}，使用Mock模式: {e}")
                set_llm_client(MockLLMClient())
        
        self.engine = get_coach_engine()
        self.problem_library = get_problem_library()
        self.current_session: Optional[Session] = None
    
    def _build_llm_config(self, provider: str, api_key: str = None, model: str = None) -> LLMConfig:
        """构建LLM配置"""
        # 默认模型
        default_models = {
            "qwen": "qwen-plus",
            "openai": "gpt-4",
            "anthropic": "claude-3-sonnet-20240229"
        }
        
        return LLMConfig(
            model=model or default_models.get(provider, "qwen-plus"),
            api_key=api_key,
            temperature=0.7,
            max_tokens=2000
        )
    
    def start_session(self, problem: Problem = None) -> str:
        """开始新会话"""
        self.current_session = self.engine.create_session()
        
        if problem is None:
            # 随机选择一道题
            problem = self.problem_library.get_random_problem()
        
        return self.engine.set_problem(self.current_session.session_id, problem)
    
    def send_message(self, message: str) -> str:
        """发送消息"""
        if not self.current_session:
            return "请先开始一个会话。"
        
        return self.engine.process_input(
            self.current_session.session_id,
            message
        )
    
    def get_status(self) -> dict:
        """获取当前状态"""
        if not self.current_session:
            return {"status": "no_session"}
        
        session = self.current_session
        return {
            "session_id": session.session_id,
            "phase": session.phase.value,
            "problem": session.problem.title if session.problem else None,
            "guidance_attempts": session.guidance_state.attempt_count,
            "followup_progress": f"{session.followup_state.questions_asked}/{session.followup_state.total_questions}"
        }
    
    def run_cli(self):
        """运行CLI交互"""
        self._print_welcome()
        
        while True:
            try:
                # 显示提示符
                prompt = self._get_prompt()
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n再见！祝你面试顺利！🎉")
                    break
                
                if user_input.lower() in ['help', 'h', '?']:
                    self._print_help()
                    continue
                
                if user_input.lower() == 'status':
                    self._print_status()
                    continue
                
                if user_input.lower() == 'problems':
                    self._list_problems()
                    continue
                
                if user_input.lower().startswith('select '):
                    problem_name = user_input[7:].strip()
                    self._select_problem(problem_name)
                    continue
                
                if user_input.lower() == 'new':
                    self._start_new_problem()
                    continue
                
                # 正常对话
                if not self.current_session:
                    print("\n请先选择一道题目。输入 'problems' 查看题目列表，或 'new' 开始随机题目。")
                    continue
                
                response = self.send_message(user_input)
                print(f"\n{response}\n")
                
            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n出错了: {e}")
    
    def _print_welcome(self):
        """打印欢迎信息"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║          🎯 算法面试教练 - Interview Coach                    ║
╠══════════════════════════════════════════════════════════════╣
║  我是你的算法面试教练！                                        ║
║  我会通过提问引导你思考，帮助你提升解题能力。                    ║
║                                                              ║
║  命令：                                                       ║
║    problems  - 查看题目列表                                   ║
║    select X  - 选择题目                                       ║
║    new       - 随机开始新题目                                 ║
║    status    - 查看当前状态                                   ║
║    help      - 帮助                                          ║
║    quit      - 退出                                          ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    def _print_help(self):
        """打印帮助信息"""
        print("""
📚 帮助信息

【交互方式】
- 直接输入你的代码或思路
- 说 "帮助" 或 "提示" 获取引导
- 说 "跳过" 或 "下一题" 跳过当前题目

【命令】
- problems  : 显示所有可用题目
- select X  : 选择名称包含 X 的题目
- new       : 随机选择一道新题目
- status    : 显示当前会话状态
- quit/exit : 退出程序

【流程说明】
1. 选择题目后，尝试给出你的代码
2. 如果正确，我会问你3个追问问题
3. 如果有问题，我会引导你思考
4. 最多5次引导后，我会给出答案和讲解
""")
    
    def _print_status(self):
        """打印当前状态"""
        status = self.get_status()
        
        if status.get("status") == "no_session":
            print("\n⚪ 当前没有进行中的会话")
            return
        
        phase_names = {
            "waiting_problem": "等待选题",
            "waiting_code": "等待代码",
            "guiding": "引导中",
            "followup": "追问中",
            "teaching": "教学中",
            "completed": "已完成"
        }
        
        print(f"""
📊 当前状态
─────────────────────────
题目：{status['problem'] or '未选择'}
阶段：{phase_names.get(status['phase'], status['phase'])}
引导尝试：{status['guidance_attempts']}/5
追问进度：{status['followup_progress']}
─────────────────────────
""")
    
    def _list_problems(self):
        """列出所有题目"""
        problems = self.problem_library.list_problems()
        
        print("\n📋 可用题目")
        print("─" * 50)
        
        for i, p in enumerate(problems, 1):
            difficulty_icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(p.difficulty, "⚪")
            print(f"{i}. {difficulty_icon} {p.title}")
        
        print("─" * 50)
        print("输入 'select 题目名称' 选择题目\n")
    
    def _select_problem(self, name: str):
        """选择题目"""
        problem = self.problem_library.get_problem_by_title(name)
        
        if not problem:
            print(f"\n❌ 没有找到包含 '{name}' 的题目")
            print("输入 'problems' 查看所有可用题目\n")
            return
        
        opening = self.start_session(problem)
        print(f"\n{opening}\n")
    
    def _start_new_problem(self):
        """开始新的随机题目"""
        opening = self.start_session()  # 不传problem则随机选择
        print(f"\n{opening}\n")
    
    def _get_prompt(self) -> str:
        """获取输入提示符"""
        if not self.current_session:
            return ">>> "
        
        phase = self.current_session.phase.value
        phase_icons = {
            "waiting_code": "💻",
            "guiding": "🎯",
            "followup": "❓",
            "teaching": "📖",
            "completed": "✅"
        }
        icon = phase_icons.get(phase, "🤖")
        return f"{icon} >>> "


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="算法面试教练",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python -m src.main                        # Mock模式（开发测试）
  python -m src.main --provider qwen        # 使用通义千问
  python -m src.main --provider qwen --model qwen-max  # 使用qwen-max模型
  python -m src.main --provider openai      # 使用OpenAI
  python -m src.main -p "两数之和"           # 指定题目

环境变量：
  DASHSCOPE_API_KEY / QWEN_API_KEY  - 通义千问API密钥
  OPENAI_API_KEY                    - OpenAI API密钥
  ANTHROPIC_API_KEY                 - Anthropic API密钥
        """
    )
    parser.add_argument("--problem", "-p", help="指定题目名称")
    parser.add_argument("--random", "-r", action="store_true", help="随机选择题目")
    parser.add_argument(
        "--provider", 
        default="mock", 
        choices=["mock", "qwen", "openai", "anthropic"], 
        help="LLM提供商（默认: mock）"
    )
    parser.add_argument("--model", "-m", help="模型名称（如 qwen-plus, qwen-max, gpt-4）")
    parser.add_argument("--api-key", help="API密钥（也可通过环境变量设置）")
    
    args = parser.parse_args()
    
    # 创建应用
    app = InterviewCoachApp(
        provider=args.provider,
        api_key=args.api_key,
        model=args.model
    )
    
    # 如果指定了题目，直接开始
    if args.problem:
        problem = app.problem_library.get_problem_by_title(args.problem)
        if problem:
            opening = app.start_session(problem)
            print(f"\n{opening}\n")
        else:
            print(f"找不到题目: {args.problem}")
            app._list_problems()
    elif args.random:
        opening = app.start_session()
        print(f"\n{opening}\n")
    
    # 运行CLI
    app.run_cli()


if __name__ == "__main__":
    main()
