# 面试讲述稿：Regional Air Route Marketing Science

## 60 秒版本

这个项目不是把 MMM 当成主模型，而是把它放进一个更完整的 Marketing Science 决策系统里。业务问题是：加拿大 regional airports 在预算有限时，应该支持哪些航线、投多少钱、以及怎么验证营销真的有效。

我先搭了 route-month panel，把公开机场流量、机场 movements、route supply evidence 和 hub competition 做成基础层。然后做 route opportunity score，区分 active-route scale/test、relaunch feasibility 和 benchmark/control route。因为没有真实营销 spend，我没有声称真实 MMM attribution，而是做了 scenario-based response curve 和 sensitivity/recovery analysis，测试不同营销生成机制下模型能不能恢复正确渠道排序和预算方向。最后用 constrained optimizer 输出预算组合，并设计 matched-route / geo-lift 的验证方案。

最后推荐的 planning case 是 `portfolio_value_500k`：分配 CAD 500,000 到 7 条路线，预计 incremental passenger proxy 约 16,936，route-health lift 22.2 points。关键 caveat 是：预算方向比精确渠道排序更稳，真实 channel ROI 必须等 partner spend 和 booking outcome 数据来验证。

## 项目亮点

- 我没有把模拟营销数据包装成真实因果结论。
- 我把 MMM 从主模型降级成 response module，前面先解决 route sustainability 和 supply/demand context。
- 我做了 sensitivity/recovery analysis，验证在不同 spend mechanism 和 true effect strength 下模型能不能恢复正确 channel ordering。
- 我把模型结果接到了 budget optimizer 和 experiment design，形成完整业务闭环。

## 推荐结果怎么讲

- 推荐 case：`portfolio_value_500k`。
- 总预算：CAD 500,000。
- Funded routes：7。
- Relaunch budget：CAD 75,000。
- Incremental passenger proxy：16,936。
- Route-health lift：22.2 points。

推荐 allocation：

- `YKF_YEG`: CAD 100,000, scale_defend
- `YKF_YYC`: CAD 100,000, test_and_learn
- `YKF_YVR`: CAD 75,000, relaunch_feasibility
- `YXU_YYC`: CAD 75,000, test_and_learn
- `YXX_YYC`: CAD 75,000, test_and_learn
- `YXX_YEG`: CAD 50,000, maintain
- `YLW_YVR`: CAD 25,000, maintain

这里最值得讲的是 `YKF_YVR`。它在 opportunity score 里很高，但期末状态是 inactive，所以我没有把它当普通 media lift route，而是标成 capacity-gated relaunch feasibility test。这说明模型不是只会排序，还会尊重业务约束。

## Sensitivity Analysis 怎么讲

- Controlled/saturation top-channel recovery：58%。
- Naive raw-spend top-channel recovery：8%。
- Controlled/saturation budget-efficiency ratio：93%。
- Naive raw-spend budget-efficiency ratio：82%。

我的解释是：如果只看 simulated marketing data，不能说某个 channel 一定最好。但 recovery analysis 显示，MMM-like 模型在预算方向上比 naive model 稳很多。所以这个项目的价值不是 claiming exact channel ROI，而是帮助业务做 route-level portfolio direction 和实验优先级。

## 如果面试官追问为什么不用真实 MMM

我会说：真实 MMM 需要真实 spend variation 和 outcome data。这个项目用公开数据做 portfolio-level prototype，所以我把 Meridian 放成未来可替换组件：当拿到 route-level spend、booking、search conversion、load factor 和 fare/yield 数据后，可以把当前 scenario response module 替换成 Meridian，并用 Vertex Pipelines 做可复现训练和比较。

## 如果面试官追问最大风险

最大风险是 simulated marketing response 不能证明真实因果效应。我的处理方式是三层 guardrail：第一，所有 passenger 都叫 proxy；第二，用 sensitivity/recovery analysis 暴露 channel ranking 的脆弱性；第三，最终推荐必须进入 matched-route 或 geo-lift 实验，而不是直接规模化投放。

## 下一步可以怎么扩展

- 接入真实 route-level booking/search data。
- 用更完整 schedule archive 改善 route-active labels。
- 在 Vertex AI 上做 pipeline 化训练和 scenario registry。
- 拿真实 spend 后接入 Google Meridian。
- 做一个 route portfolio dashboard 给商业团队使用。
