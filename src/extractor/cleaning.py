# 没有信息量的套话：包含这些短语的 indication 会被代码直接删掉（全部用小写，方便比较）
NON_INFORMATIVE = {"condition listed above", "as directed by the physician", "as directed"}

def clean_indications(items: list[str]) -> list[str]:
    """后处理：删掉套话，并去掉重复项（忽略大小写和首尾空格）。"""
    cleaned = []  # 保存保留下来的条目
    seen = set()  # 记录已经出现过的条目（小写形式），用来去重
    for item in items:  # 逐条检查模型给出的 indication
        key = item.strip().lower()  # 统一成小写、去掉首尾空格，便于比较
        if not key:  # 空字符串
            continue  # 跳过
        if any(p in key for p in NON_INFORMATIVE):  # 只要包含任意一个套话短语
            continue  # 就丢掉这一条
        if key in seen:  # 之前已经出现过（例如 "Acne" 和 "acne"）
            continue  # 丢掉重复项
        seen.add(key)  # 记录下来
        cleaned.append(item.strip())  # 保留原始大小写，只去掉首尾空格
    return cleaned  # 返回清洗后的列表