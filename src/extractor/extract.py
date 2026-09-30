from openai import OpenAI                           # OpenAI 客户端
from dotenv import load_dotenv                      # 读取 .env
from extractor.schema import DrugLabel              # schema 在 schema.py 里
from extractor.cleaning import clean_indications    # 过滤函数在 cleaning.py 里
from functools import lru_cache # 缓存函数结果，避免重复调用模型
import logging

# 系统提示词：告诉模型它的角色，以及只能使用原文里的信息（减少编造）
SYSTEM_PROMPT = "You extract structured information from FDA drug labels. Only use information present in the text."

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    """Create the OpenAI client on first use, not at import time."""
    return OpenAI()


def extract_drug_label_info(
    label_text: str,
    *,
    clean: bool = True,
    client: OpenAI | None = None,
) -> DrugLabel | None:
    """
    Extract structured information from a drug label text using the OpenAI API.

    clean=True 时对 indications 做规则过滤；clean=False 返回模型原始结果（用来对比过滤效果）。
    client 可注入，测试时传入假客户端，生产环境留空即可。
    Returns None if the model refuses or its output can't be parsed into DrugLabel.
    """
    client = client or get_client()


    # Responses API + 结构化输出：SDK 会把 DrugLabel 转成 JSON Schema 发给模型
    response = client.responses.parse(  
        model="gpt-4o-mini",  # 使用的模型
        temperature=0,  # 降低随机性；但它解决不了“两种答案本来就一样合理”的歧义，歧义要在输入侧解决
        input=[  # 对话消息列表
            {"role": "system", "content": SYSTEM_PROMPT},  # 系统消息：规则
            {"role": "user", "content": label_text}  # 用户消息：标签文本
        ],
        text_format=DrugLabel,  # 要求模型按 DrugLabel 的结构输出
    )

    # Responses API 没有 .choices（那是 Chat Completions API 的写法）
    # output_parsed 已经是 DrugLabel 实例；output_text 是模型返回的原始 JSON 字符串
    result = response.output_parsed  # 取出解析好的结果
    if result is None:
        logger.warning("Could not parse model output: %s", response.output_text)
        return None

    # if clean:  # 需要清洗时
    #     result.indications = clean_indications(result.indications)  # 用规则过滤 indications
    # return result  # 返回 DrugLabel 实例

    if clean:
        result = result.model_copy(
            update={"indications": clean_indications(result.indications)}
        )
    return result