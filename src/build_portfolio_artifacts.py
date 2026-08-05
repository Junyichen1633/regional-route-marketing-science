"""Build final portfolio artifacts from generated project outputs."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

ROUTE_SCORE_FILE = PROCESSED_DIR / "route_opportunity_score_v0.csv"
BUDGET_CASE_FILE = PROCESSED_DIR / "budget_optimization_case_summary_v0.csv"
BUDGET_ALLOCATION_FILE = PROCESSED_DIR / "budget_optimization_allocations_v0.csv"
SENSITIVITY_FILE = PROCESSED_DIR / "marketing_sensitivity_summary_v0.csv"
EXPERIMENT_FILE = PROCESSED_DIR / "experiment_design_plan_v0.csv"

CASE_STUDY_FILE = REPORTS_DIR / "final_portfolio_case_study.md"
TALK_TRACK_FILE = REPORTS_DIR / "interview_talk_track_cn.md"
SNAPSHOT_FILE = OUTPUTS_DIR / "final_portfolio_snapshot.md"

RECOMMENDED_CASE_ID = "portfolio_value_500k"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def to_float(value: str | None, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def money(value: object) -> str:
    return f"CAD {float(value):,.0f}"


def number(value: object, digits: int = 0) -> str:
    return f"{float(value):,.{digits}f}"


def pct(value: object, digits: int = 0) -> str:
    return f"{float(value):.{digits}%}"


def recommended_case() -> dict[str, str]:
    for row in read_csv(BUDGET_CASE_FILE):
        if row["case_id"] == RECOMMENDED_CASE_ID:
            return row
    raise ValueError(f"Missing recommended case: {RECOMMENDED_CASE_ID}")


def recommended_allocations() -> list[dict[str, str]]:
    rows = [row for row in read_csv(BUDGET_ALLOCATION_FILE) if row["case_id"] == RECOMMENDED_CASE_ID]
    return sorted(rows, key=lambda row: (-to_float(row["campaign_budget_cad"]), row["route_id"]))


def top_routes(limit: int = 8) -> list[dict[str, str]]:
    rows = [row for row in read_csv(ROUTE_SCORE_FILE) if row["model_role"] == "target"]
    rows.sort(key=lambda row: to_float(row["marketing_support_priority_score_v0"]), reverse=True)
    return rows[:limit]


def sensitivity_averages() -> dict[str, dict[str, float]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(SENSITIVITY_FILE):
        groups[row["model_spec"]].append(row)

    output = {}
    for model_spec, rows in groups.items():
        output[model_spec] = {
            "top_channel_recovery": sum(to_float(row["top_channel_recovery_rate"]) for row in rows) / len(rows),
            "top2_overlap": sum(to_float(row["mean_top2_budget_direction_overlap"]) for row in rows) / len(rows),
            "budget_efficiency": sum(to_float(row["mean_budget_efficiency_ratio"]) for row in rows) / len(rows),
            "rank_corr": sum(to_float(row["mean_spearman_rank_corr"]) for row in rows) / len(rows),
        }
    return output


def experiment_rows() -> list[dict[str, str]]:
    return sorted(read_csv(EXPERIMENT_FILE), key=lambda row: (-to_float(row["campaign_budget_cad"]), row["route_id"]))


def route_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Rank | Route | Status | Priority | Sustainability | Recommendation |",
        "|---:|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['opportunity_rank_target_only']} | {row['route_id']} | {row['end_of_period_route_status']} | "
            f"{to_float(row['marketing_support_priority_score_v0']):.1f} | "
            f"{to_float(row['route_sustainability_score_v0']):.1f} | {row['recommendation']} |"
        )
    return lines


def allocation_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Route | Budget | Bucket | Incremental passenger proxy | Health lift pts |",
        "|---|---:|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['route_id']} | {money(row['campaign_budget_cad'])} | {row['decision_bucket']} | "
            f"{number(row['incremental_passenger_proxy'])} | {to_float(row['incremental_route_health_points']):.1f} |"
        )
    return lines


def sensitivity_table(averages: dict[str, dict[str, float]]) -> list[str]:
    order = ["controlled_saturation", "controlled_adstock", "naive_raw_spend"]
    lines = [
        "| Model spec | Top-channel recovery | Top-2 direction overlap | Budget-efficiency ratio | Rank corr. |",
        "|---|---:|---:|---:|---:|",
    ]
    for model_spec in order:
        row = averages[model_spec]
        lines.append(
            f"| {model_spec} | {pct(row['top_channel_recovery'])} | {pct(row['top2_overlap'])} | "
            f"{pct(row['budget_efficiency'])} | {row['rank_corr']:.2f} |"
        )
    return lines


def experiment_table(rows: list[dict[str, str]]) -> list[str]:
    lines = [
        "| Route | Design | Primary metric | Comparison routes | Power readiness |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        controls = ", ".join(
            control
            for control in [row["comparison_route_1"], row["comparison_route_2"], row["comparison_route_3"]]
            if control
        )
        lines.append(
            f"| {row['route_id']} | {row['experiment_design']} | {row['primary_metric']} | "
            f"{controls} | {row['power_readiness']} |"
        )
    return lines


def build_case_study() -> str:
    case = recommended_case()
    allocations = recommended_allocations()
    sensitivities = sensitivity_averages()
    experiments = experiment_rows()
    routes = top_routes()

    lines = [
        "# Regional Air Route Marketing Science",
        "",
        "## Executive Summary",
        "",
        "This project builds a marketing science decision-support system for Canadian regional air routes. The goal is to decide which routes deserve marketing support, how much budget to allocate, and how the recommendation should be validated before scaling.",
        "",
        "The project is deliberately not framed as a pure MMM. MMM-style response modeling is one component inside a broader route sustainability, response simulation, optimization, and experimentation workflow.",
        "",
        "## Business Decision",
        "",
        "Decision question:",
        "",
        "> Which regional air routes should receive incremental marketing investment, and how should a fixed budget be allocated to maximize sustainable demand?",
        "",
        "Primary decision owner:",
        "",
        "- Regional airport commercial/marketing team, in partnership with airline network planning.",
        "",
        "Decision cadence:",
        "",
        "- Quarterly route-support planning with campaign-level validation windows.",
        "",
        "## System Architecture",
        "",
        "```mermaid",
        "flowchart LR",
        '  A["Public data and route evidence"] --> B["Route-month panel"]',
        '  B --> C["Route supply and opportunity score"]',
        '  C --> D["Marketing response scenarios"]',
        '  D --> E["Sensitivity and recovery analysis"]',
        '  D --> F["Budget optimizer"]',
        '  E --> F',
        '  F --> G["Experiment design"]',
        '  G --> H["Scale / maintain / stop decision"]',
        "```",
        "",
        "## Data Strategy",
        "",
        "The project uses public airport context and sourced route-supply evidence. Because route-level passenger demand and marketing spend are usually proprietary, the project explicitly labels unobserved outcomes as proxies and simulated marketing as scenario-based.",
        "",
        "Key modeling grain:",
        "",
        "```text",
        "route_id x month",
        "```",
        "",
        "Core limitations:",
        "",
        "- Route-month passenger counts are not directly observed.",
        "- Marketing spend is simulated, not real measured spend.",
        "- Direct frequency is event-based and incomplete.",
        "- Route-active labels come from sourced route events, not a complete schedule archive.",
        "",
        "## Route Opportunity Readout",
        "",
    ]
    lines.extend(route_table(routes))
    lines.extend(
        [
            "",
            "The important modeling choice is that `YKF_YVR` is not treated as an ordinary active-route scale candidate. It is a relaunch feasibility candidate because the route has strong demand context and strategic fit, but the end-of-period status is inactive.",
            "",
            "## Marketing Sensitivity Readout",
            "",
        ]
    )
    lines.extend(sensitivity_table(sensitivities))
    lines.extend(
        [
            "",
            "Interpretation:",
            "",
            "- Budget direction is more stable than exact channel ranking.",
            "- Simulated marketing data should not be used to claim definitive channel ROI.",
            "- The MMM-like controlled/saturation specification improves budget direction, but channel ranking remains fragile when effects are weak or channels are bought as a bundle.",
            "- Google Meridian or a similar MMM component would be appropriate only after real spend variation and route-level outcomes are available.",
            "",
            "## Recommended Budget Allocation",
            "",
            f"Recommended planning case: `{RECOMMENDED_CASE_ID}`",
            "",
            f"- Total budget: {money(case['total_budget_cad'])}",
            f"- Allocated budget: {money(case['allocated_budget_cad'])}",
            f"- Funded routes: {case['funded_routes']}",
            f"- Relaunch budget: {money(case['relaunch_budget_cad'])}",
            f"- Incremental passenger proxy: {number(case['incremental_passenger_proxy'])}",
            f"- Incremental route-health lift: {to_float(case['incremental_route_health_points']):.1f} points",
            f"- Cost per incremental proxy passenger: {money(case['cost_per_incremental_passenger_proxy_cad'])}",
            "",
        ]
    )
    lines.extend(allocation_table(allocations))
    lines.extend(
        [
            "",
            "## Validation Plan",
            "",
        ]
    )
    lines.extend(experiment_table(experiments))
    lines.extend(
        [
            "",
            "Validation principle:",
            "",
            "- Active routes should be tested with matched-route or geo-lift designs where booking or search-conversion data is available.",
            "- Relaunch routes should be treated as two-stage capacity-gated feasibility tests.",
            "- Public data can prioritize tests, but partner data is required to validate incrementality.",
            "",
            "## Vertex AI / Meridian Path",
            "",
            "A production-grade version would use Google Cloud as follows:",
            "",
            "- Store route-month panel, campaign spend, and booking outcomes in BigQuery.",
            "- Use Vertex AI Pipelines to rebuild features, score route opportunity, run response models, and optimize budgets.",
            "- Use Vertex Experiments to compare route-health, passenger-growth, and portfolio-value objectives.",
            "- Use Meridian only when real marketing spend and route-level outcomes exist; until then, keep the response module scenario-based.",
            "- Export recommendations to Looker Studio or a lightweight dashboard for planning review.",
            "",
            "## Interview Framing",
            "",
            "This project demonstrates L4-level product data science because it handles an ambiguous business problem under imperfect data, avoids false causal claims, builds a complete decision workflow, and proposes an experiment design to validate recommendations.",
            "",
            "Strongest takeaways:",
            "",
            "- Reframed MMM as a component, not the whole project.",
            "- Built a route-level decision system despite public-data constraints.",
            "- Used sensitivity/recovery simulation to test what simulated marketing data can and cannot prove.",
            "- Connected modeling output to budget allocation and validation design.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_talk_track_cn() -> str:
    case = recommended_case()
    allocations = recommended_allocations()
    sensitivities = sensitivity_averages()

    allocation_lines = [
        f"- `{row['route_id']}`: {money(row['campaign_budget_cad'])}, {row['decision_bucket']}"
        for row in allocations
    ]

    lines = [
        "# 面试讲述稿：Regional Air Route Marketing Science",
        "",
        "## 60 秒版本",
        "",
        "这个项目不是把 MMM 当成主模型，而是把它放进一个更完整的 Marketing Science 决策系统里。业务问题是：加拿大 regional airports 在预算有限时，应该支持哪些航线、投多少钱、以及怎么验证营销真的有效。",
        "",
        "我先搭了 route-month panel，把公开机场流量、机场 movements、route supply evidence 和 hub competition 做成基础层。然后做 route opportunity score，区分 active-route scale/test、relaunch feasibility 和 benchmark/control route。因为没有真实营销 spend，我没有声称真实 MMM attribution，而是做了 scenario-based response curve 和 sensitivity/recovery analysis，测试不同营销生成机制下模型能不能恢复正确渠道排序和预算方向。最后用 constrained optimizer 输出预算组合，并设计 matched-route / geo-lift 的验证方案。",
        "",
        "最后推荐的 planning case 是 `portfolio_value_500k`：分配 CAD 500,000 到 7 条路线，预计 incremental passenger proxy 约 16,936，route-health lift 22.2 points。关键 caveat 是：预算方向比精确渠道排序更稳，真实 channel ROI 必须等 partner spend 和 booking outcome 数据来验证。",
        "",
        "## 项目亮点",
        "",
        "- 我没有把模拟营销数据包装成真实因果结论。",
        "- 我把 MMM 从主模型降级成 response module，前面先解决 route sustainability 和 supply/demand context。",
        "- 我做了 sensitivity/recovery analysis，验证在不同 spend mechanism 和 true effect strength 下模型能不能恢复正确 channel ordering。",
        "- 我把模型结果接到了 budget optimizer 和 experiment design，形成完整业务闭环。",
        "",
        "## 推荐结果怎么讲",
        "",
        f"- 推荐 case：`portfolio_value_500k`。",
        f"- 总预算：{money(case['total_budget_cad'])}。",
        f"- Funded routes：{case['funded_routes']}。",
        f"- Relaunch budget：{money(case['relaunch_budget_cad'])}。",
        f"- Incremental passenger proxy：{number(case['incremental_passenger_proxy'])}。",
        f"- Route-health lift：{to_float(case['incremental_route_health_points']):.1f} points。",
        "",
        "推荐 allocation：",
        "",
    ]
    lines.extend(allocation_lines)
    lines.extend(
        [
            "",
            "这里最值得讲的是 `YKF_YVR`。它在 opportunity score 里很高，但期末状态是 inactive，所以我没有把它当普通 media lift route，而是标成 capacity-gated relaunch feasibility test。这说明模型不是只会排序，还会尊重业务约束。",
            "",
            "## Sensitivity Analysis 怎么讲",
            "",
            f"- Controlled/saturation top-channel recovery：{pct(sensitivities['controlled_saturation']['top_channel_recovery'])}。",
            f"- Naive raw-spend top-channel recovery：{pct(sensitivities['naive_raw_spend']['top_channel_recovery'])}。",
            f"- Controlled/saturation budget-efficiency ratio：{pct(sensitivities['controlled_saturation']['budget_efficiency'])}。",
            f"- Naive raw-spend budget-efficiency ratio：{pct(sensitivities['naive_raw_spend']['budget_efficiency'])}。",
            "",
            "我的解释是：如果只看 simulated marketing data，不能说某个 channel 一定最好。但 recovery analysis 显示，MMM-like 模型在预算方向上比 naive model 稳很多。所以这个项目的价值不是 claiming exact channel ROI，而是帮助业务做 route-level portfolio direction 和实验优先级。",
            "",
            "## 如果面试官追问为什么不用真实 MMM",
            "",
            "我会说：真实 MMM 需要真实 spend variation 和 outcome data。这个项目用公开数据做 portfolio-level prototype，所以我把 Meridian 放成未来可替换组件：当拿到 route-level spend、booking、search conversion、load factor 和 fare/yield 数据后，可以把当前 scenario response module 替换成 Meridian，并用 Vertex Pipelines 做可复现训练和比较。",
            "",
            "## 如果面试官追问最大风险",
            "",
            "最大风险是 simulated marketing response 不能证明真实因果效应。我的处理方式是三层 guardrail：第一，所有 passenger 都叫 proxy；第二，用 sensitivity/recovery analysis 暴露 channel ranking 的脆弱性；第三，最终推荐必须进入 matched-route 或 geo-lift 实验，而不是直接规模化投放。",
            "",
            "## 下一步可以怎么扩展",
            "",
            "- 接入真实 route-level booking/search data。",
            "- 用更完整 schedule archive 改善 route-active labels。",
            "- 在 Vertex AI 上做 pipeline 化训练和 scenario registry。",
            "- 拿真实 spend 后接入 Google Meridian。",
            "- 做一个 route portfolio dashboard 给商业团队使用。",
        ]
    )
    return "\n".join(lines) + "\n"


def build_snapshot() -> str:
    case = recommended_case()
    sensitivities = sensitivity_averages()
    lines = [
        "# Final Portfolio Snapshot",
        "",
        f"- Recommended case: `{RECOMMENDED_CASE_ID}`",
        f"- Budget: {money(case['allocated_budget_cad'])}",
        f"- Funded routes: {case['funded_routes']}",
        f"- Incremental passenger proxy: {number(case['incremental_passenger_proxy'])}",
        f"- Route-health lift: {to_float(case['incremental_route_health_points']):.1f} points",
        f"- Controlled/saturation top-channel recovery: {pct(sensitivities['controlled_saturation']['top_channel_recovery'])}",
        f"- Controlled/saturation budget-efficiency ratio: {pct(sensitivities['controlled_saturation']['budget_efficiency'])}",
        "",
        "Core claim: the project supports route-level portfolio direction and experiment prioritization under public-data constraints; it does not claim observed causal channel ROI.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    CASE_STUDY_FILE.write_text(build_case_study(), encoding="utf-8")
    TALK_TRACK_FILE.write_text(build_talk_track_cn(), encoding="utf-8")
    SNAPSHOT_FILE.write_text(build_snapshot(), encoding="utf-8")

    print(f"Wrote {CASE_STUDY_FILE}")
    print(f"Wrote {TALK_TRACK_FILE}")
    print(f"Wrote {SNAPSHOT_FILE}")


if __name__ == "__main__":
    main()
