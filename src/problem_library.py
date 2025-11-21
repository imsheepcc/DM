"""
示例题库

包含几道经典算法题，用于测试和演示
"""

from src.models import Problem
from typing import List, Dict


# ==================== 题目定义 ====================

TWO_SUM = Problem(
    title="两数之和 (Two Sum)",
    description="""给定一个整数数组 nums 和一个整数目标值 target，请你在该数组中找出和为目标值 target 的那两个整数，并返回它们的数组下标。

你可以假设每种输入只会对应一个答案。但是，数组中同一个元素在答案里不能重复出现。

示例：
输入：nums = [2, 7, 11, 15], target = 9
输出：[0, 1]
解释：因为 nums[0] + nums[1] == 9 ，返回 [0, 1]""",
    difficulty="easy",
    expected_complexity="O(n) 时间, O(n) 空间",
    test_cases=[
        {"input": "nums = [2, 7, 11, 15], target = 9", "output": "[0, 1]"},
        {"input": "nums = [3, 2, 4], target = 6", "output": "[1, 2]"},
        {"input": "nums = [3, 3], target = 6", "output": "[0, 1]"}
    ],
    solution_hints=[
        "考虑用哈希表存储已见过的数字",
        "对于每个数字，检查 target - num 是否在哈希表中"
    ]
)


VALID_PARENTHESES = Problem(
    title="有效的括号 (Valid Parentheses)",
    description="""给定一个只包括 '('，')'，'{'，'}'，'['，']' 的字符串 s ，判断字符串是否有效。

有效字符串需满足：
1. 左括号必须用相同类型的右括号闭合。
2. 左括号必须以正确的顺序闭合。
3. 每个右括号都有一个对应的相同类型的左括号。

示例：
输入：s = "()"
输出：true

输入：s = "()[]{}"
输出：true

输入：s = "(]"
输出：false""",
    difficulty="easy",
    expected_complexity="O(n) 时间, O(n) 空间",
    test_cases=[
        {"input": 's = "()"', "output": "true"},
        {"input": 's = "()[]{}"', "output": "true"},
        {"input": 's = "(]"', "output": "false"},
        {"input": 's = "([)]"', "output": "false"}
    ],
    solution_hints=[
        "使用栈来匹配括号",
        "遇到左括号入栈，遇到右括号出栈匹配"
    ]
)


REVERSE_LINKED_LIST = Problem(
    title="反转链表 (Reverse Linked List)",
    description="""给你单链表的头节点 head ，请你反转链表，并返回反转后的链表。

示例：
输入：head = [1,2,3,4,5]
输出：[5,4,3,2,1]

输入：head = [1,2]
输出：[2,1]

输入：head = []
输出：[]""",
    difficulty="easy",
    expected_complexity="O(n) 时间, O(1) 空间",
    test_cases=[
        {"input": "head = [1,2,3,4,5]", "output": "[5,4,3,2,1]"},
        {"input": "head = [1,2]", "output": "[2,1]"},
        {"input": "head = []", "output": "[]"}
    ],
    solution_hints=[
        "使用三个指针：prev, curr, next",
        "迭代过程中逐个反转指针方向"
    ]
)


BINARY_SEARCH = Problem(
    title="二分查找 (Binary Search)",
    description="""给定一个 n 个元素有序的（升序）整型数组 nums 和一个目标值 target，写一个函数搜索 nums 中的 target，如果目标值存在返回下标，否则返回 -1。

示例：
输入: nums = [-1,0,3,5,9,12], target = 9
输出: 4
解释: 9 出现在 nums 中并且下标为 4

输入: nums = [-1,0,3,5,9,12], target = 2
输出: -1
解释: 2 不存在 nums 中因此返回 -1""",
    difficulty="easy",
    expected_complexity="O(log n) 时间, O(1) 空间",
    test_cases=[
        {"input": "nums = [-1,0,3,5,9,12], target = 9", "output": "4"},
        {"input": "nums = [-1,0,3,5,9,12], target = 2", "output": "-1"}
    ],
    solution_hints=[
        "维护左右边界，每次取中间",
        "根据中间值与目标的比较缩小范围"
    ]
)


MERGE_TWO_SORTED_LISTS = Problem(
    title="合并两个有序链表 (Merge Two Sorted Lists)",
    description="""将两个升序链表合并为一个新的升序链表并返回。新链表是通过拼接给定的两个链表的所有节点组成的。

示例：
输入：l1 = [1,2,4], l2 = [1,3,4]
输出：[1,1,2,3,4,4]

输入：l1 = [], l2 = []
输出：[]

输入：l1 = [], l2 = [0]
输出：[0]""",
    difficulty="easy",
    expected_complexity="O(n+m) 时间, O(1) 空间",
    test_cases=[
        {"input": "l1 = [1,2,4], l2 = [1,3,4]", "output": "[1,1,2,3,4,4]"},
        {"input": "l1 = [], l2 = []", "output": "[]"},
        {"input": "l1 = [], l2 = [0]", "output": "[0]"}
    ],
    solution_hints=[
        "使用虚拟头节点简化处理",
        "比较两个链表当前节点，选择较小的"
    ]
)


MAXIMUM_SUBARRAY = Problem(
    title="最大子数组和 (Maximum Subarray)",
    description="""给你一个整数数组 nums ，请你找出一个具有最大和的连续子数组（子数组最少包含一个元素），返回其最大和。

子数组是数组中的一个连续部分。

示例：
输入：nums = [-2,1,-3,4,-1,2,1,-5,4]
输出：6
解释：连续子数组 [4,-1,2,1] 的和最大，为 6。

输入：nums = [1]
输出：1

输入：nums = [5,4,-1,7,8]
输出：23""",
    difficulty="medium",
    expected_complexity="O(n) 时间, O(1) 空间",
    test_cases=[
        {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6"},
        {"input": "nums = [1]", "output": "1"},
        {"input": "nums = [5,4,-1,7,8]", "output": "23"}
    ],
    solution_hints=[
        "动态规划：dp[i] 表示以 i 结尾的最大子数组和",
        "Kadane算法：维护当前和与最大和"
    ]
)


CLIMBING_STAIRS = Problem(
    title="爬楼梯 (Climbing Stairs)",
    description="""假设你正在爬楼梯。需要 n 阶你才能到达楼顶。

每次你可以爬 1 或 2 个台阶。你有多少种不同的方法可以爬到楼顶呢？

示例：
输入：n = 2
输出：2
解释：有两种方法可以爬到楼顶。
1. 1 阶 + 1 阶
2. 2 阶

输入：n = 3
输出：3
解释：有三种方法可以爬到楼顶。
1. 1 阶 + 1 阶 + 1 阶
2. 1 阶 + 2 阶
3. 2 阶 + 1 阶""",
    difficulty="easy",
    expected_complexity="O(n) 时间, O(1) 空间",
    test_cases=[
        {"input": "n = 2", "output": "2"},
        {"input": "n = 3", "output": "3"},
        {"input": "n = 4", "output": "5"}
    ],
    solution_hints=[
        "动态规划：f(n) = f(n-1) + f(n-2)",
        "这实际上是斐波那契数列"
    ]
)


COIN_CHANGE = Problem(
    title="零钱兑换 (Coin Change)",
    description="""给你一个整数数组 coins ，表示不同面额的硬币；以及一个整数 amount ，表示总金额。

计算并返回可以凑成总金额所需的最少的硬币个数。如果没有任何一种硬币组合能组成总金额，返回 -1。

你可以认为每种硬币的数量是无限的。

示例：
输入：coins = [1, 2, 5], amount = 11
输出：3 
解释：11 = 5 + 5 + 1

输入：coins = [2], amount = 3
输出：-1

输入：coins = [1], amount = 0
输出：0""",
    difficulty="medium",
    expected_complexity="O(amount * len(coins)) 时间",
    test_cases=[
        {"input": "coins = [1, 2, 5], amount = 11", "output": "3"},
        {"input": "coins = [2], amount = 3", "output": "-1"},
        {"input": "coins = [1], amount = 0", "output": "0"}
    ],
    solution_hints=[
        "完全背包问题",
        "dp[i] 表示凑成金额 i 所需的最少硬币数"
    ]
)


# ==================== 题库管理 ====================

class ProblemLibrary:
    """题库管理"""
    
    def __init__(self):
        self.problems: Dict[str, Problem] = {}
        self._load_default_problems()
    
    def _load_default_problems(self):
        """加载默认题目"""
        default_problems = [
            TWO_SUM,
            VALID_PARENTHESES,
            REVERSE_LINKED_LIST,
            BINARY_SEARCH,
            MERGE_TWO_SORTED_LISTS,
            MAXIMUM_SUBARRAY,
            CLIMBING_STAIRS,
            COIN_CHANGE
        ]
        
        for problem in default_problems:
            self.add_problem(problem)
    
    def add_problem(self, problem: Problem):
        """添加题目"""
        # 使用标题作为key
        key = problem.title.lower().replace(" ", "_")
        self.problems[key] = problem
    
    def get_problem(self, key: str) -> Problem:
        """获取题目"""
        return self.problems.get(key.lower().replace(" ", "_"))
    
    def get_problem_by_title(self, title: str) -> Problem:
        """通过标题获取题目"""
        for problem in self.problems.values():
            if title.lower() in problem.title.lower():
                return problem
        return None
    
    def list_problems(self, difficulty: str = None) -> List[Problem]:
        """列出题目"""
        problems = list(self.problems.values())
        
        if difficulty:
            problems = [p for p in problems if p.difficulty == difficulty]
        
        return problems
    
    def get_random_problem(self, difficulty: str = None) -> Problem:
        """随机获取一道题"""
        import random
        problems = self.list_problems(difficulty)
        return random.choice(problems) if problems else None


# ==================== 全局实例 ====================

_problem_library: ProblemLibrary = None

def get_problem_library() -> ProblemLibrary:
    """获取题库单例"""
    global _problem_library
    if _problem_library is None:
        _problem_library = ProblemLibrary()
    return _problem_library
