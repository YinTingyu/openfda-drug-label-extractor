import re  # regular expressions, used to strip HTML tags and extra spaces

# 字段白名单：只把和抽取任务相关的段落发给模型
# 其余字段（药代动力学、临床试验、SPL_PRODUCT_DATA_ELEMENTS、ID、*_table 等）
# 既浪费 token，又会污染输出（例如把 "BARK" 误当成剂型）
FIELDS = [
    "indications_and_usage",       # 适应症（处方药 + OTC 都有）
    "purpose",                     # OTC 药的“用途”段落
    "contraindications",           # 禁忌症（处方药用这个字段名）
    "do_not_use",                  # 禁忌症（OTC 药用这个字段名，语义同上）
    "warnings",                    # 警告 / 慎用
    "ask_doctor",                  # 使用前需咨询医生的情况
    "dosage_and_administration",   # 用法用量，也是判断剂型的主要依据
    "dosage_forms_and_strengths",  # 剂型与规格（处方药）
    # 额外两个字段（不需要可以删掉）：
    "stop_use",                    # 停药条件，对应 SafetyInfo.stop_use_conditions
    "warnings_and_cautions",       # 新版处方药标签用这个名字代替 "warnings"
]

_TAG = re.compile(r"<[^>]+>")  # 匹配任意 HTML 标签，例如 <td>、</table>
_SPACE = re.compile(r"\s+")    # 匹配连续的空白（空格、换行、制表符）



def field_to_text(value) -> str:
    """把 openFDA 的一个字段转成干净的文本，不管它是什么类型。"""
    if value is None:                        # 字段不存在
        return ""                            # 返回空字符串
    if isinstance(value, str):               # 字符串，例如 effective_time = "20150109"
        # 注意：不能对字符串用 " ".join()，那样会把每个字符拆开，变成 "2 0 1 5 ..."
        no_tags = _TAG.sub(" ", value)       # 把 HTML 标签替换成空格
        return _SPACE.sub(" ", no_tags).strip()  # 多个空白合并成一个，并去掉首尾空白
    if isinstance(value, dict):              # 字典，例如 openfda = {"brand_name": [...], ...}
        lines = []                           # 用来收集每一行 "key: value"
        for k, v in value.items():           # 遍历字典的每个键值对
            text = field_to_text(v)         # 递归：把值也转成文本
            if text:                         # 跳过空值
                lines.append(f"{k}: {text}") # 保存为 "key: value" 格式
        return "\n".join(lines)              # 每个键值对占一行
    if isinstance(value, (list, tuple)):     # 列表，openFDA 的大部分段落都是 ["一段文字"]
        parts = []                           # 用来收集每个元素的文本
        for v in value:                      # 遍历列表元素
            text = field_to_text(v)         # 递归：元素本身可能是字符串 / 字典
            if text:                         # 跳过空元素
                parts.append(text)           # 保存
        return " ".join(parts)               # 这里 join 的是“字符串列表”，所以是安全的
    return str(value)                        # 其他类型（数字、布尔值）直接转字符串


def label_to_text(label: dict, fields: list[str] = FIELDS) -> str:
    """把一份 openFDA 标签中白名单内的字段合并成一段文本，发给模型。"""
    sections = []                            # 用来收集每个段落
    for key in fields:                       # 按白名单顺序遍历字段
        text = field_to_text(label.get(key))  # .get() 在字段不存在时返回 None，不会报 KeyError
        if text:                             # 这份标签没有该字段、或内容为空时跳过
            sections.append(f"{key.upper()}:\n{text}")  # 段落格式："字段名大写:\n内容"
    return "\n\n".join(sections)             # 段落之间空一行



# how to deal with the case when the key doesn't exist in the dictionary? Use .get(key, default) to avoid KeyError.
# do not assume that the key exists, length of the list, or has fallback values.

def get_drug_name(label: dict) -> str | None:
    """
    Extracts the drug name from the label dictionary.
    
    Args:
        label (dict): A dictionary containing drug label information.

    Returns:
        str: The drug name.
    """
    # .get(key, default) is used to avoid KeyError if the key doesn't exist
    openfda = label.get("openfda", {})  # 取 openfda 子字典，没有就用空字典
    # 按优先级找名字：通用名 → 品牌名 → 成分名；`or` 会返回第一个非空的值，都为空时返回 []
    names = openfda.get("generic_name") or openfda.get("brand_name") or openfda.get("substance_name") or []
    return ", ".join(names) if names else None  # 多个名字用逗号连接；一个都没有就返回占位文字