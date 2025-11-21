#!/usr/bin/env python3
"""
通义千问API连接测试脚本

使用方式：
    # 设置环境变量
    export DASHSCOPE_API_KEY="your-api-key"
    
    # 运行测试
    python test_qwen.py
"""

import os
import sys

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm_client import create_llm_client, LLMConfig


def test_qwen_connection():
    """测试通义千问API连接"""
    
    print("=" * 50)
    print("通义千问 API 连接测试")
    print("=" * 50)
    
    # 检查API Key
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not api_key:
        print("\n❌ 未找到API密钥")
        print("请设置环境变量: export DASHSCOPE_API_KEY='your-key'")
        return False
    
    print(f"\n✓ 找到API密钥: {api_key[:8]}...{api_key[-4:]}")
    
    # 测试不同模型
    models = ["qwen-turbo", "qwen-plus"]
    
    for model in models:
        print(f"\n--- 测试模型: {model} ---")
        
        try:
            config = LLMConfig(
                model=model,
                temperature=0.7,
                max_tokens=100
            )
            client = create_llm_client("qwen", config)
            
            # 简单测试
            response = client.call(
                "你好，请用一句话介绍自己。",
                system_prompt="你是一位友好的助手。"
            )
            
            print(f"✓ 响应: {response[:100]}...")
            
            # 测试JSON输出
            json_response = client.call_json(
                '请返回JSON格式: {"greeting": "你的问候", "status": "ok"}',
                system_prompt="你是一个助手，总是返回有效的JSON。"
            )
            
            print(f"✓ JSON解析: {json_response}")
            
        except Exception as e:
            print(f"❌ 错误: {e}")
            continue
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
    return True


def test_interview_flow():
    """测试面试流程（完整流程测试）"""
    
    print("\n" + "=" * 50)
    print("面试流程测试")
    print("=" * 50)
    
    try:
        from src.llm_client import set_llm_client
        from src.coach_engine import CoachEngine
        from src.models import create_problem
        
        # 创建千问客户端
        config = LLMConfig(model="qwen-plus", temperature=0.7, max_tokens=1500)
        client = create_llm_client("qwen", config)
        set_llm_client(client)
        
        # 创建引擎
        engine = CoachEngine()
        session = engine.create_session()
        
        # 创建测试题目
        problem = create_problem(
            title="两数之和",
            description="""给定一个整数数组 nums 和一个整数目标值 target，
请你在该数组中找出和为目标值 target 的那两个整数，并返回它们的数组下标。

示例：
输入：nums = [2,7,11,15], target = 9
输出：[0,1]
解释：因为 nums[0] + nums[1] == 9 ，返回 [0, 1]""",
            difficulty="easy",
            expected_complexity="O(n)",
            test_cases=[
                {"input": "nums=[2,7,11,15], target=9", "output": "[0,1]"},
                {"input": "nums=[3,2,4], target=6", "output": "[1,2]"}
            ]
        )
        
        # 开始会话
        print("\n1. 设置题目...")
        opening = engine.set_problem(session.session_id, problem)
        print(f"教练: {opening[:200]}...")
        
        # 测试用户请求帮助
        print("\n2. 用户请求帮助...")
        response = engine.process_input(session.session_id, "我不太会，能给我一些提示吗？")
        print(f"教练: {response[:200]}...")
        
        # 测试用户回答
        print("\n3. 用户回答...")
        response = engine.process_input(session.session_id, "我可以用两个循环遍历吗？")
        print(f"教练: {response[:200]}...")
        
        print("\n✓ 面试流程测试通过!")
        return True
        
    except Exception as e:
        print(f"\n❌ 面试流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 先测试连接
    if test_qwen_connection():
        # 再测试完整流程
        test_interview_flow()
