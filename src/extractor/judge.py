"""LLM judge：判断同一字段里的两条内容是否表达同一个事实。"""

import re                                   # 正则：用于 exact 基线的归一化
from functools import lru_cache             # 缓存：OpenAI 客户端只创建一次
from typing import Literal                  # 限定 label 只能取三个值

from dotenv import load_dotenv              # 从 .env 读取 OPENAI_API_KEY
from openai import OpenAI                   # OpenAI 官方 SDK
from pydantic import BaseModel, Field       # 定义 judge 的结构化输出

Label = Literal["equivalent", "partial", "not_equivalent"]  # 三种判定结果

# judge 的系统提示词：定义三种标签和判断规则（和 judge_cases.json 顶部的 labels / rules 保持一致）
JUDGE_PROMPT = """You compare two items, a and b, extracted from the same field of an FDA drug label.
Decide whether they state the same fact. Work through the steps in order and stop at the first that applies.

Step 1 - Strip wrapping text from both sides. Ignore:
  - the action the field already implies ("do not use", "ask a doctor before use if",
    "stop use and ask a doctor if"). In a contraindications item, "Use in the eyes" means
    "do not use in the eyes".
  - purpose or framing phrases ("first aid to help prevent infection in X" means X;
    "treatment of infections ... in X" means X)
  - trailing actions that only restate what to do ("..., discontinue use and seek assistance")
  - wording, punctuation, case; unit conversions; medical synonyms
  Do NOT strip extra specific facts (e.g. which routes of injection are forbidden).

Step 2 - If what remains is the same fact: equivalent.

Step 3 - not_equivalent if any of these differ, even when one side is a subset of the other:
  - the item itself (a different condition, reaction, or instruction)
  - a number or threshold in value (1 week == 7 days; 4 days != 7 days)
  - severity (minor vs serious burns; blurred vision vs vision loss)
  - substance (povidone-iodine vs iodine)
  - strength (caution vs prohibition)
  - direction of the condition (worsen vs improve). The field's implied "do not" is not a direction.

Step 4 - partial if the facts overlap but one side covers more:
  - a list vs one of its items
  - a broader vs narrower condition ("conjunctivitis" vs "bacterial conjunctivitis")
  - a headline vs the same headline plus extra specific facts

Step 5 - Otherwise: not_equivalent. Sharing a topic alone is not enough for equivalent or partial."""


class JudgeVerdict(BaseModel):  # judge 返回的结构
    reason: str = Field(description="One short sentence explaining the decision.")  # 先写理由再给标签，判断更稳定
    label: Label  # 最终判定


@lru_cache(maxsize=1)  # 只在第一次调用时创建客户端；import 本模块时不需要 API key（测试更好写）
def _client() -> OpenAI:
    load_dotenv()  # 加载 .env
    return OpenAI()  # 创建客户端


def llm_judge(field: str, a: str, b: str, model: str = "gpt-4o-mini") -> JudgeVerdict:
    """调用 LLM 判断 a 和 b 在 field 字段里是否等价。"""
    response = _client().responses.parse(  # 结构化输出调用
        model=model,  # 使用的模型
        temperature=0,  # 判定要尽量稳定
        input=[  # 消息列表
            {"role": "system", "content": JUDGE_PROMPT},  # 规则
            {"role": "user", "content": f"field: {field}\na: {a}\nb: {b}"},  # 待判断的一对
        ],
        text_format=JudgeVerdict,  # 按 JudgeVerdict 解析
    )
    if response.output_parsed is None:  # 模型拒绝或解析失败
        raise ValueError(f"judge output could not be parsed: {response.output_text}")  # 直接报错，不静默吞掉
    return response.output_parsed  # 返回 JudgeVerdict


def _normalise(text: str) -> str:
    """小写、去标点、合并空白。"""
    text = text.lower()  # 统一小写
    text = re.sub(r"[^\w\s]", " ", text)  # 标点换成空格
    return re.sub(r"\s+", " ", text).strip()  # 多个空白合并成一个


def exact_judge(field: str, a: str, b: str, model: str = "") -> JudgeVerdict:
    """基线：归一化后完全相同才算等价，永远不会输出 partial。不调用 API。"""
    same = _normalise(a) == _normalise(b)  # 归一化后比较
    return JudgeVerdict(  # 包装成和 LLM judge 一样的结构，方便统一处理
        reason="exact match after normalisation" if same else "strings differ after normalisation",  # 说明
        label="equivalent" if same else "not_equivalent",  # 判定
    )