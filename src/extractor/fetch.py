import requests # HTTP library, used to call the openFDA API

# 调用 openFDA 药品标签接口，limit=5 表示只取 5 份标签
drug = requests.get("https://api.fda.gov/drug/label.json", params={"limit": 5})

drug.raise_for_status()  # 如果接口返回错误（如 404、429 限流），在这里直接报错，而不是后面出现难懂的 KeyError

data = drug.json()  # 把返回的 JSON 文本解析成 Python 字典

labels = data["results"]  # 标签列表在 "results" 键下，每个元素是一份标签（dict）

