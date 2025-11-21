# 算法面试教练 V2

一个对话式的算法面试练习系统，通过苏格拉底式教学帮助用户提升解题能力。

## 🎯 核心特点

- **自然对话**：用户界面呈现为普通聊天，无阶段显示
- **动态引导**：所有回复由LLM实时生成，不使用预设模板
- **智能评估**：自动判断代码正确性并决定下一步行动
- **循序渐进**：最多5次引导机会，之后给出详细教学
- **多LLM支持**：支持通义千问、OpenAI、Anthropic等多种LLM

## 📋 流程设计

```
用户提交代码
    │
    ├─── 正确 ───► 追问3个问题 ───► 完成
    │
    ├─── 错误 ───► 开始引导对话
    │
    └─── 请求帮助 ───► 开始引导对话
                          │
                     ┌────┴────┐
                     │ 动态引导 │◄──┐
                     └────┬────┘    │
                          │         │
                      答对了？      │
                      │    │        │
                     是    否───────┘
                      │    (次数<5)
                      ▼
                    追问     次数≥5
                             │
                             ▼
                   给出答案+教学 ───► 结束
```

## 🚀 快速开始

### 安装

```bash
cd interview-coach-v2
pip install -r requirements.txt
```

### 运行

```bash
# Mock模式（开发/测试，不需要API密钥）
python -m src.main

# 使用通义千问（推荐）
export DASHSCOPE_API_KEY="your-key"  # 或 QWEN_API_KEY
python -m src.main --provider qwen

# 使用通义千问 qwen-max 模型
python -m src.main --provider qwen --model qwen-max

# 使用OpenAI
export OPENAI_API_KEY="your-key"
python -m src.main --provider openai

# 使用Anthropic
export ANTHROPIC_API_KEY="your-key"
python -m src.main --provider anthropic

# 指定题目启动
python -m src.main --provider qwen -p "两数之和"

# 随机题目启动
python -m src.main --provider qwen --random
```

### 测试API连接

```bash
export DASHSCOPE_API_KEY="your-key"
python test_qwen.py
```

### CLI命令

- `problems` - 查看题目列表
- `select X` - 选择题目
- `new` - 随机开始新题目
- `status` - 查看当前状态
- `help` - 帮助
- `quit` - 退出

## 📁 项目结构

```
interview-coach-v2/
├── src/
│   ├── models.py          # 核心数据模型
│   ├── prompt_library.py  # Prompt生成库
│   ├── llm_client.py      # LLM客户端（支持Mock/Qwen/OpenAI/Anthropic）
│   ├── coach_engine.py    # 核心教练引擎
│   ├── problem_library.py # 题库
│   └── main.py            # 主应用入口
├── tests/
│   └── test_coach.py      # 测试套件
├── config/
│   └── settings.py        # 配置管理
├── test_qwen.py           # 通义千问API测试脚本
├── requirements.txt
└── README.md
```

## 🔧 核心模块

### 1. 数据模型 (`models.py`)

- `Session`: 会话状态管理
- `SessionPhase`: 会话阶段枚举
- `GuidanceState`: 引导状态追踪（包含尝试次数）
- `FollowUpState`: 追问状态追踪

### 2. Prompt库 (`prompt_library.py`)

- 意图识别Prompt
- 代码评估Prompt
- 引导对话Prompt（支持3级提示强度）
- 追问生成Prompt
- 教学Prompt

### 3. LLM客户端 (`llm_client.py`)

- `MockLLMClient`: 开发/测试用
- `QwenClient`: 通义千问（推荐）
- `OpenAIClient`: OpenAI API
- `AnthropicClient`: Anthropic API

### 4. 教练引擎 (`coach_engine.py`)

核心控制器，处理：
- 意图识别
- 代码评估
- 状态转换
- 对话生成

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/

# 测试通义千问连接
python test_qwen.py
```

## ⚙️ 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DASHSCOPE_API_KEY` | 通义千问API密钥 | - |
| `QWEN_API_KEY` | 通义千问API密钥(别名) | - |
| `OPENAI_API_KEY` | OpenAI密钥 | - |
| `ANTHROPIC_API_KEY` | Anthropic密钥 | - |

### 命令行参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--provider` | LLM提供商 | `qwen`, `openai`, `anthropic`, `mock` |
| `--model` | 模型名称 | `qwen-plus`, `qwen-max`, `gpt-4` |
| `--problem`, `-p` | 指定题目 | `"两数之和"` |
| `--random`, `-r` | 随机题目 | - |
| `--api-key` | API密钥 | - |

### 通义千问模型选择

| 模型 | 特点 | 推荐场景 |
|------|------|----------|
| `qwen-turbo` | 快速、成本低 | 测试、简单对话 |
| `qwen-plus` | 平衡 | **日常使用（默认）** |
| `qwen-max` | 最强能力 | 复杂推理 |

## 📚 题库

内置8道经典算法题：

| 题目 | 难度 |
|------|------|
| 两数之和 | 🟢 Easy |
| 有效的括号 | 🟢 Easy |
| 反转链表 | 🟢 Easy |
| 二分查找 | 🟢 Easy |
| 合并两个有序链表 | 🟢 Easy |
| 最大子数组和 | 🟡 Medium |
| 爬楼梯 | 🟢 Easy |
| 零钱兑换 | 🟡 Medium |

## 🔒 安全机制

- LLM被明确指示不能直接给出答案
- 多层Prompt约束防止答案泄露
- 只有在5次引导失败后才会给出完整解答

## 🛠️ 扩展

### 添加新题目

```python
from src.models import Problem
from src.problem_library import get_problem_library

new_problem = Problem(
    title="新题目",
    description="题目描述...",
    difficulty="medium",
    expected_complexity="O(n)",
    test_cases=[...]
)

library = get_problem_library()
library.add_problem(new_problem)
```

### 使用自定义LLM

```python
from src.llm_client import BaseLLMClient, set_llm_client

class MyCustomLLM(BaseLLMClient):
    def call(self, prompt, system_prompt=None):
        # 你的实现
        pass
    
    def call_json(self, prompt, system_prompt=None):
        # 你的实现
        pass

set_llm_client(MyCustomLLM())
```

## 📝 License

MIT
