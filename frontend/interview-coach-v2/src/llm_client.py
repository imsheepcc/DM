"""
LLM客户端 (V2)

支持：
- 真实API调用
- Mock模式用于开发/测试
- 统一的接口
"""

import json
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM配置"""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 1500
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """
        调用LLM
        
        Args:
            prompt: 用户prompt
            system_prompt: 系统prompt（可选）
            
        Returns:
            LLM的回复文本
        """
        pass
    
    @abstractmethod
    def call_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """
        调用LLM并解析JSON响应
        
        Args:
            prompt: 用户prompt
            system_prompt: 系统prompt（可选）
            
        Returns:
            解析后的JSON字典
        """
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API客户端"""
    
    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()
        self.api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env var or pass in config.")
        
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.config.base_url
            )
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
    
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """调用OpenAI API"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def call_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """调用并解析JSON"""
        response = self.call(prompt, system_prompt)
        return self._parse_json(response)
    
    def _parse_json(self, text: str) -> Dict:
        """解析JSON，处理可能的格式问题"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON块
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试找到第一个 { 和最后一个 }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"Failed to parse JSON from response: {text[:200]}...")
        return {"reply": text, "error": "json_parse_failed"}


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API客户端"""
    
    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig(model="claude-3-sonnet-20240229")
        self.api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY env var or pass in config.")
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
    
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """调用Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=system_prompt or "",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def call_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """调用并解析JSON"""
        response = self.call(prompt, system_prompt)
        return self._parse_json(response)
    
    def _parse_json(self, text: str) -> Dict:
        """解析JSON"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        
        return {"reply": text, "error": "json_parse_failed"}


class QwenClient(BaseLLMClient):
    """
    通义千问 API客户端
    
    使用阿里云DashScope API
    文档: https://help.aliyun.com/document_detail/2712195.html
    """
    
    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig(
            model="qwen-plus",  # 可选: qwen-turbo, qwen-plus, qwen-max
            temperature=0.7,
            max_tokens=2000
        )
        self.api_key = self.config.api_key or os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "通义千问 API key not found. "
                "Set DASHSCOPE_API_KEY or QWEN_API_KEY env var or pass in config."
            )
        
        # 支持两种调用方式
        self.use_openai_compatible = self.config.base_url is not None
        
        if self.use_openai_compatible:
            # 使用OpenAI兼容接口
            try:
                import openai
                self.client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.config.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
            except ImportError:
                raise ImportError("Please install openai: pip install openai")
        else:
            # 使用DashScope原生SDK
            try:
                import dashscope
                dashscope.api_key = self.api_key
                self.dashscope = dashscope
            except ImportError:
                # 如果没有dashscope，回退到HTTP调用
                self.dashscope = None
                logger.info("DashScope SDK not found, using HTTP API")
    
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """调用通义千问API"""
        if self.use_openai_compatible:
            return self._call_openai_compatible(prompt, system_prompt)
        elif self.dashscope:
            return self._call_dashscope(prompt, system_prompt)
        else:
            return self._call_http(prompt, system_prompt)
    
    def _call_openai_compatible(self, prompt: str, system_prompt: str = None) -> str:
        """使用OpenAI兼容接口"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Qwen OpenAI-compatible API call failed: {e}")
            raise
    
    def _call_dashscope(self, prompt: str, system_prompt: str = None) -> str:
        """使用DashScope原生SDK"""
        from dashscope import Generation
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = Generation.call(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                result_format='message'
            )
            
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                raise Exception(f"API error: {response.code} - {response.message}")
        except Exception as e:
            logger.error(f"DashScope API call failed: {e}")
            raise
    
    def _call_http(self, prompt: str, system_prompt: str = None) -> str:
        """使用HTTP直接调用"""
        import requests
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "result_format": "message"
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            result = response.json()
            
            if "output" in result:
                return result["output"]["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Unexpected response format: {result}")
        except Exception as e:
            logger.error(f"Qwen HTTP API call failed: {e}")
            raise
    
    def call_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """调用并解析JSON"""
        # 增强prompt以确保返回JSON
        json_prompt = prompt
        if "JSON" not in prompt and "json" not in prompt:
            json_prompt = prompt + "\n\n请确保返回有效的JSON格式。"
        
        response = self.call(json_prompt, system_prompt)
        return self._parse_json(response)
    
    def _parse_json(self, text: str) -> Dict:
        """解析JSON，处理可能的格式问题"""
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON块
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试提取```块
        code_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if code_match:
            try:
                return json.loads(code_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # 尝试找到第一个 { 和最后一个 }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"Failed to parse JSON from response: {text[:200]}...")
        return {"reply": text, "error": "json_parse_failed"}


class MockLLMClient(BaseLLMClient):
    """
    Mock LLM客户端
    
    用于开发和测试，模拟LLM的行为
    """
    
    def __init__(self, responses: Dict[str, Any] = None):
        """
        Args:
            responses: 预设的响应映射，key可以是关键词
        """
        self.responses = responses or {}
        self.call_history = []
        self.default_responses = self._build_default_responses()
    
    def _build_default_responses(self) -> Dict:
        """构建默认的模拟响应"""
        return {
            "intent_recognition": {
                "intent": "answer_question",
                "reply": "我理解你的想法。让我们继续探讨一下...",
                "reasoning": "用户在回答问题"
            },
            "code_evaluation_correct": {
                "evaluation": "correct",
                "reply": "代码看起来是正确的！让我问你一个深入的问题：这个算法的时间复杂度是多少？",
                "issues": [],
                "test_result": "测试用例验证通过"
            },
            "code_evaluation_incorrect": {
                "evaluation": "incorrect",
                "reply": "我看了你的代码，有些地方值得再想想。如果输入是空数组，会发生什么？你能用第一个测试用例在脑中运行一下你的代码吗？",
                "issues": ["边界条件处理", "逻辑可能有误"],
                "test_result": "测试用例验证未通过"
            },
            "guidance": {
                "user_on_right_track": False,
                "user_current_understanding": "用户还在探索中",
                "what_user_is_missing": "核心数据结构的选择",
                "reply": "你的思路很有意思。让我问你一个问题：有没有什么数据结构可以帮助我们快速查找？",
                "hint_used": "暗示数据结构方向"
            },
            "guidance_correct": {
                "user_on_right_track": True,
                "user_current_understanding": "用户理解了核心思路",
                "what_user_is_missing": "需要将思路转化为代码",
                "reply": "对！你抓住了关键点。那你能把这个思路转化为代码吗？",
                "hint_used": "肯定正确方向"
            },
            "followup": {
                "question": "如果输入数组非常大，有上百万个元素，你的解法还能高效工作吗？",
                "expected_direction": "讨论空间复杂度和大数据处理",
                "difficulty": "medium"
            },
            "followup_evaluation_good": {
                "answer_quality": "good",
                "correct_answer": "时间复杂度O(n)，空间复杂度O(n)",
                "user_understanding": "用户正确理解了复杂度",
                "reply": "很好的分析！确实是这样。那么，有没有办法优化空间复杂度呢？",
                "next_question": "空间复杂度优化"
            },
            "followup_evaluation_incorrect": {
                "answer_quality": "incorrect",
                "correct_answer": "时间复杂度O(n)，空间复杂度O(n)",
                "user_understanding": "用户对复杂度分析有误解",
                "reply": "这个分析不太对哦。让我给你一个提示：哈希表的查找操作是什么复杂度？整个数组我们遍历了几次？",
                "next_question": "重新思考时间复杂度"
            },
            "followup_evaluation_partial": {
                "answer_quality": "partial",
                "correct_answer": "时间复杂度O(n)，空间复杂度O(n)",
                "user_understanding": "用户部分理解",
                "reply": "你说对了一部分！时间复杂度确实是O(n)。那空间复杂度呢？我们用了什么额外空间？",
                "next_question": "空间复杂度分析"
            },
            "teaching": """没关系，这道题确实有一定难度。让我来帮你梳理一下：

**解题思路：**
这道题的关键是使用哈希表来优化查找。对于每个数字，我们检查目标值减去当前数字是否已经在哈希表中。

**参考代码：**
```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

**关键点：**
1. 用空间换时间，O(n)复杂度
2. 边界条件：空数组、无解情况
3. 这个"哈希表记录已见元素"的技巧可以用于很多类似问题

继续加油！这类题目多练几道就会有感觉了。""",
            "help_request": {
                "reply": "没问题，让我给你一些提示。这道题的关键是思考：如何快速判断一个数是否存在？有什么数据结构可以帮助我们？",
                "hint_type": "引导数据结构思考"
            }
        }
    
    def call(self, prompt: str, system_prompt: str = None) -> str:
        """模拟LLM调用"""
        self.call_history.append({
            "prompt": prompt,
            "system_prompt": system_prompt
        })
        
        # 根据prompt内容返回不同响应
        response = self._get_mock_response(prompt)
        
        if isinstance(response, dict):
            return json.dumps(response, ensure_ascii=False)
        return response
    
    def call_json(self, prompt: str, system_prompt: str = None) -> Dict:
        """模拟JSON调用"""
        response = self.call(prompt, system_prompt)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"reply": response}
    
    def _get_mock_response(self, prompt: str) -> Any:
        """根据prompt内容获取模拟响应"""
        prompt_lower = prompt.lower()
        
        # 检查预设响应（用户自定义的优先）
        for key, response in self.responses.items():
            if key.lower() in prompt_lower:
                return response
        
        # 根据任务类型返回默认响应
        # 注意顺序：更具体的先匹配
        
        # 代码评估 - 默认返回incorrect，除非代码看起来正确
        if "严格评估代码" in prompt or "评估代码" in prompt or "逻辑正确性" in prompt:
            # 检查是否包含正确的哈希表解法特征
            if ("seen" in prompt or "hash" in prompt_lower or "字典" in prompt) and \
               ("complement" in prompt or "target - " in prompt or "target-" in prompt):
                return self.default_responses["code_evaluation_correct"]
            # 默认返回incorrect
            return self.default_responses["code_evaluation_incorrect"]
        
        # 追问评估 - 默认返回incorrect，除非答案包含正确关键词
        if "严格评估回答" in prompt or ("追问" in prompt and "评估" in prompt):
            user_answer_section = prompt.split("【用户回答】")[-1] if "【用户回答】" in prompt else ""
            # 检查用户回答是否包含正确关键词
            if "o(n)" in user_answer_section.lower() or "O(n)" in user_answer_section:
                if "o(1)" in user_answer_section.lower() or "O(1)" in user_answer_section:
                    return self.default_responses["followup_evaluation_partial"]
                return self.default_responses["followup_evaluation_good"]
            return self.default_responses["followup_evaluation_incorrect"]
        
        # 追问生成
        if "追问" in prompt and ("/3" in prompt or "个追问" in prompt):
            return self.default_responses["followup"]
        
        # 教学（5次尝试后）
        if "教学" in prompt or "给出答案" in prompt or "需要给出答案和教学" in prompt:
            return self.default_responses["teaching"]
        
        # 引导对话 - 默认返回false，除非用户明确提到正确思路
        if "引导状态" in prompt or "严格评估并引导" in prompt:
            user_input_section = prompt.split("【用户最新输入】")[-1] if "【用户最新输入】" in prompt else ""
            # 只有明确提到哈希表/字典才判断为正确
            if "哈希" in user_input_section or "hash" in user_input_section.lower() or \
               "字典" in user_input_section or "dict" in user_input_section.lower():
                return self.default_responses["guidance_correct"]
            return self.default_responses["guidance"]
        
        # 帮助请求
        if "帮助" in prompt or "help" in prompt_lower or "请求帮助" in prompt:
            return self.default_responses["help_request"]
        
        # 意图识别 - 最后匹配
        if "意图" in prompt or "intent" in prompt_lower or "理解用户意图" in prompt:
            return self.default_responses["intent_recognition"]
        
        # 默认返回
        return self.default_responses["intent_recognition"]
    
    def set_response(self, key: str, response: Any):
        """设置特定关键词的响应"""
        self.responses[key] = response
    
    def get_call_history(self) -> list:
        """获取调用历史"""
        return self.call_history
    
    def clear_history(self):
        """清空调用历史"""
        self.call_history = []


# ==================== 工厂函数 ====================

def create_llm_client(
    provider: str = "mock",
    config: LLMConfig = None
) -> BaseLLMClient:
    """
    创建LLM客户端
    
    Args:
        provider: "openai", "anthropic", "qwen", or "mock"
        config: LLM配置
        
    Returns:
        LLM客户端实例
        
    示例:
        # 使用通义千问
        client = create_llm_client("qwen", LLMConfig(
            model="qwen-plus",  # qwen-turbo, qwen-plus, qwen-max
            api_key="your-api-key"
        ))
    """
    if provider == "openai":
        return OpenAIClient(config)
    elif provider == "anthropic":
        return AnthropicClient(config)
    elif provider == "qwen":
        return QwenClient(config)
    elif provider == "mock":
        return MockLLMClient()
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: openai, anthropic, qwen, mock")


# ==================== 全局实例管理 ====================

_llm_client: Optional[BaseLLMClient] = None

def get_llm_client() -> BaseLLMClient:
    """获取全局LLM客户端"""
    global _llm_client
    if _llm_client is None:
        # 默认使用Mock
        _llm_client = MockLLMClient()
    return _llm_client

def set_llm_client(client: BaseLLMClient):
    """设置全局LLM客户端"""
    global _llm_client
    _llm_client = client
