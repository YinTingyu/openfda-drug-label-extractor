# tests/test_cleaning.py
import pytest  # 测试框架（用 parametrize 时必须导入）
from extractor.cleaning import clean_indications  # 被测函数

def test_keeps_normal_items():  # 正常条目原样保留
    assert clean_indications(["acne", "boils"]) == ["acne", "boils"]

@pytest.mark.parametrize("phrase", [  # 同一个测试用多组输入各跑一次
    "Condition listed above",          # 套话 1（大写开头，顺便测大小写不敏感）
    "As directed by the physician",    # 套话 2
    "use as directed",                 # 套话出现在句子中间
])
def test_removes_non_informative(phrase):  # 含套话的条目被删掉
    assert clean_indications(["acne", phrase]) == ["acne"]

def test_dedup_ignores_case_and_spaces():  # 去重：忽略大小写和首尾空格，保留第一次出现的写法
    assert clean_indications(["Acne", " acne ", "ACNE"]) == ["Acne"]

def test_strips_whitespace():  # 输出去掉首尾空格
    assert clean_indications(["  acne  "]) == ["acne"]

def test_drops_empty_and_blank():  # 空字符串和纯空格都被跳过
    assert clean_indications(["", "   ", "acne"]) == ["acne"]

def test_empty_list():  # 边界：空输入返回空列表，不报错
    assert clean_indications([]) == []

def test_preserves_order():  # 保留原顺序
    assert clean_indications(["boils", "acne", "boils"]) == ["boils", "acne"]

def test_does_not_modify_input():  # 副作用：不改动传进来的列表
    items = [" acne ", "acne"]  # 准备输入
    clean_indications(items)  # 调用函数
    assert items == [" acne ", "acne"]  # 原列表应保持不变

# 子串匹配误杀，精确匹配漏杀
def test_known_limitation_substring_match():  # 已知局限：子串匹配会误删有效条目
    # 这个测试记录的是“当前行为”，不是“理想行为”；以后改成更精确的匹配时，要同步修改这个测试
    assert clean_indications(["headache (use as directed)"]) == []


