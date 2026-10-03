"""跑 data/judge_cases.json，比较 judge 的判定和人工标签，输出混淆矩阵。

用法（在项目根目录）：
    uv run python scripts/validate_judge.py                  # 用 LLM judge
    uv run python scripts/validate_judge.py --judge exact    # 用 exact match 基线，不调用 API
    uv run python scripts/validate_judge.py --model gpt-4o   # 换 judge 模型
"""

import argparse                             # 解析命令行参数
import json                                 # 读写 JSON
from collections import Counter, defaultdict  # 计数
from datetime import datetime               # 生成输出文件名
from pathlib import Path                    # 路径处理

from extractor.judge import exact_judge, llm_judge  # 两种 judge

LABELS = ["equivalent", "partial", "not_equivalent"]  # 混淆矩阵的行列顺序
SHORT = {"equivalent": "equiv", "partial": "partial", "not_equivalent": "not_eq"}  # 表头缩写，保证对齐
ROOT = Path(__file__).resolve().parent.parent  # 项目根目录（scripts/ 的上一层）


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the LLM judge against judge_cases.json")  # 命令行说明
    parser.add_argument("--cases", default=ROOT / "data" / "judge_cases.json", type=Path)  # case 文件路径
    parser.add_argument("--judge", choices=["llm", "exact"], default="llm")  # 选择 judge
    parser.add_argument("--model", default="gpt-4o-mini")  # LLM judge 用的模型
    parser.add_argument("--out-dir", default=ROOT / "data" / "judge_runs", type=Path)  # 结果保存目录
    return parser.parse_args()  # 返回解析结果


def run_cases(cases: list[dict], judge, model: str) -> list[dict]:
    """逐条调用 judge，返回每条的结果。"""
    results = []  # 收集结果
    for i, case in enumerate(cases, start=1):  # 逐条跑
        verdict = judge(case["field"], case["a"], case["b"], model=model)  # 调用 judge
        results.append({  # 保存这一条
            "id": case["id"],  # case 编号
            "field": case["field"],  # 字段
            "a": case["a"],  # 预测侧文本
            "b": case["b"],  # 金标准侧文本
            "tests": case.get("tests", "untagged"),  # 这条 case 测的是什么
            "gold": case["label"],  # 人工标签
            "pred": verdict.label,  # judge 判定
            "reason": verdict.reason,  # judge 给的理由
            "correct": verdict.label == case["label"],  # 是否一致
        })
        mark = "✓" if results[-1]["correct"] else "✗"  # 进度标记
        print(f"[{i:>2}/{len(cases)}] {mark} {case['id']} gold={case['label']:<14} pred={verdict.label}")  # 打印进度
    return results  # 返回全部结果


def confusion_matrix(results: list[dict]) -> dict[str, dict[str, int]]:
    """matrix[gold][pred] = 数量。行是人工标签，列是 judge 判定。"""
    matrix = {g: {p: 0 for p in LABELS} for g in LABELS}  # 全部初始化为 0
    for r in results:  # 逐条累加
        matrix[r["gold"]][r["pred"]] += 1  # 对应格子 +1
    return matrix  # 返回矩阵


def print_matrix(matrix: dict[str, dict[str, int]]) -> None:
    """打印混淆矩阵。"""
    print("\nConfusion matrix (rows = gold, cols = judge)")  # 标题
    print(f"{'':>10}" + "".join(f"{SHORT[p]:>9}" for p in LABELS) + f"{'total':>9}")  # 表头
    for g in LABELS:  # 每一行是一个人工标签
        row = matrix[g]  # 这一行的计数
        print(f"{SHORT[g]:>10}" + "".join(f"{row[p]:>9}" for p in LABELS) + f"{sum(row.values()):>9}")  # 打印一行


def per_class_metrics(matrix: dict[str, dict[str, int]]) -> dict[str, dict[str, float | None]]:
    """每个标签的 precision / recall。分母为 0 时记为 None。"""
    metrics = {}  # 收集结果
    for label in LABELS:  # 逐个标签计算
        tp = matrix[label][label]  # 对角线：判对的
        predicted = sum(matrix[g][label] for g in LABELS)  # 这一列：judge 判成该标签的总数
        actual = sum(matrix[label].values())  # 这一行：人工标成该标签的总数
        metrics[label] = {  # 保存
            "precision": tp / predicted if predicted else None,  # judge 说是 X 的里面，真的是 X 的比例
            "recall": tp / actual if actual else None,  # 真的是 X 的里面，judge 找到的比例
            "support": actual,  # 该标签的 case 数
        }
    return metrics  # 返回


def fmt(x: float | None) -> str:
    return "  n/a" if x is None else f"{x:5.2f}"  # None 显示 n/a，数字保留两位


def main() -> None:
    args = parse_args()  # 读取命令行参数
    data = json.loads(args.cases.read_text(encoding="utf-8"))  # 读取 case 文件
    cases = data["cases"]  # case 列表
    judge = llm_judge if args.judge == "llm" else exact_judge  # 选择 judge 函数
    model = args.model if args.judge == "llm" else "n/a"  # exact 基线没有模型

    results = run_cases(cases, judge, args.model)  # 跑全部 case
    matrix = confusion_matrix(results)  # 计算混淆矩阵
    metrics = per_class_metrics(matrix)  # 计算每类指标
    accuracy = sum(r["correct"] for r in results) / len(results)  # 总准确率

    print_matrix(matrix)  # 打印矩阵
    print(f"\naccuracy: {accuracy:.2f} ({sum(r['correct'] for r in results)}/{len(results)})")  # 打印准确率
    print("\nper label:")  # 每类指标标题
    for label, m in metrics.items():  # 逐类打印
        print(f"  {label:<15} precision {fmt(m['precision'])}  recall {fmt(m['recall'])}  n={m['support']}")  # 一行

    # 最危险的错误：人工认为不等价，judge 却判为等价 → 评分时会把错误答案算成对的
    lenient = [r for r in results if r["gold"] == "not_equivalent" and r["pred"] == "equivalent"]  # 过松的判定
    print(f"\ntoo lenient (gold not_equivalent → judge equivalent): {len(lenient)}")  # 数量

    by_tag = defaultdict(Counter)  # 按 tests 标签统计正确 / 总数
    for r in results:  # 逐条统计
        by_tag[r["tests"]]["total"] += 1  # 总数 +1
        by_tag[r["tests"]]["correct"] += r["correct"]  # 正确数（True 算 1）
    print("\naccuracy by tag:")  # 标题
    for tag, c in sorted(by_tag.items(), key=lambda kv: kv[1]["correct"] / kv[1]["total"]):  # 按准确率从低到高
        print(f"  {tag:<15} {c['correct']}/{c['total']}")  # 打印

    errors = [r for r in results if not r["correct"]]  # 判错的 case
    if errors:  # 有错才打印
        print("\nerrors:")  # 标题
        for r in errors:  # 逐条打印
            print(f"  {r['id']} [{r['field']}] gold={r['gold']} pred={r['pred']}")  # 编号、字段、标签
            print(f"      a: {r['a']}")  # 预测侧
            print(f"      b: {r['b']}")  # 金标准侧
            print(f"      reason: {r['reason']}")  # judge 理由

    args.out_dir.mkdir(parents=True, exist_ok=True)  # 创建输出目录
    out_path = args.out_dir / f"{datetime.now():%Y-%m-%d_%H%M}_{args.judge}.json"  # 带时间戳的文件名
    out_path.write_text(json.dumps({  # 保存完整结果，方便以后对比不同 prompt / 模型
        "created_at": datetime.now().isoformat(timespec="seconds"),  # 运行时间
        "cases_file": str(args.cases.relative_to(ROOT)) if args.cases.is_relative_to(ROOT) else str(args.cases),  # case 文件
        "judge": args.judge,  # judge 类型
        "model": model,  # 模型
        "accuracy": accuracy,  # 准确率
        "confusion_matrix": matrix,  # 混淆矩阵
        "per_label": metrics,  # 每类指标
        "results": results,  # 每条结果
    }, indent=2, ensure_ascii=False), encoding="utf-8")  # 缩进、保留非英文字符
    print(f"\nsaved to {out_path}")  # 提示保存位置


if __name__ == "__main__":  # 直接运行脚本时才执行
    main()  # 入口