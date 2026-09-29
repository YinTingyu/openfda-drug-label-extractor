# 没有信息量的套话：包含这些短语的 indication 会被代码直接删掉（全部用小写，方便比较）
import re

# 按长度降序排列：长的模式必须先替换，否则会被短的子串截断
NON_INFORMATIVE = (
    "as directed by the physician",
    "condition listed above",
    "as directed",
)

FILTER = {"or", "and", "the", "a", "as", "for", "of", "use", "apply"}

# use residue method to filter out non-informative indications
def is_non_informative(item: str) -> bool:
    """判断一个 indication 是否没有信息量（只包含套话）。"""
    residue = item.lower() # 统一成小写
    for p in sorted(NON_INFORMATIVE, key=len, reverse=True): # 按长度降序排列，先删长的套话
        residue = residue.replace(p, "")  # 把套话短语删掉
    words = re.sub(r"[^a-z]+", " ", residue).split()  # 非字母字符都换成空格，然后按空格拆成单词
    return all(w in FILTER for w in words)  # 如果剩下的单词都在 FILTER 里，就说明没有信息量


def normalize_for_comparison(s: str) -> str:
    """Casefold and collapse whitespace, for dedup and eval comparison only.
    Never use this for the value that gets stored or displayed."""
    return " ".join(s.casefold().split())

def clean_indications(items: list[str]) -> list[str]:
    """后处理：删掉套话，并去掉重复项（忽略大小写和首尾空格）。"""
    cleaned = []  # 保存保留下来的条目
    seen = set()  # 记录已经出现过的条目（小写形式），用来去重
    
    for item in items:  # 逐条检查模型给出的 indication
        text = " ".join(item.split())  # 把换行、制表符等都换成空格
        key = normalize_for_comparison(text)  # 用于去重的标准化形式
        if not key or is_non_informative(text):  # 空字符串 或 没有信息量的套话
            continue  # 跳过
        if key in seen:  # 之前已经出现过（例如 "Acne" 和 "acne"）
            continue  # 丢掉重复项
        seen.add(key)  # 记录下来
        cleaned.append(item.strip())  # 保留原始大小写，只去掉首尾空格
    return cleaned  # 返回清洗后的列表