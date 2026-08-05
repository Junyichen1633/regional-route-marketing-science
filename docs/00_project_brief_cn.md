# 项目中文工作说明

## 一句话定位

这个项目不是“为了做 MMM 而做 MMM”，而是一个面向区域机场的 Marketing Science 决策系统：

> 在营销预算有限的情况下，判断哪些航线值得投、投多少、预期能带来多少增量需求，以及应该如何设计实验验证。

## 为什么这个题目值得做

它同时覆盖了一个完整营销科学项目需要处理的几个问题：

- 把个人观察转化成业务问题
- 判断公开数据是否足够支撑结论
- 区分预测、归因、因果和优化
- 在数据不完美时做出合理建模假设
- 输出可执行的业务建议，而不是只展示模型指标

## 三层架构

### 第一层：Route Demand / Supply Model

目标：先理解一条航线本身是否健康。

这里研究的是 baseline，也就是不额外投营销时，这条航线自然会有什么表现。

会考虑：

- 航线是否开通
- 每月航班频率
- 估算座位数
- 季节性
- 天气
- 节假日
- 附近大机场竞争
- 宏观环境
- 搜索兴趣

这一层的核心问题：

> 这条航线是需求不够，供给不够，还是被附近 hub airport 抢走了？

### 第二层：Marketing Response Model

目标：估计或模拟营销投入可能带来的增量需求。

因为真实机场或航司 marketing spend 通常不是公开数据，所以我们不能乱说“真实营销贡献”。更稳的说法是：

> 基于合理假设，构建一个 marketing response simulator，并用未来实验校准。

这里会用 MMM 的核心思想：

- adstock：广告影响会延续
- saturation：广告越投越有边际递减
- response curve：不同路线对营销的响应不同
- ROI / marginal ROI：每多投一块钱带来的增量

Google Meridian 会放在这一层，而不是整个项目的中心。

### 第三层：Budget Optimization

目标：在预算有限的情况下，给出路线级预算分配建议。

不是简单问“哪个 ROI 最高”，而是综合考虑：

- 增量乘客
- 增量利润或 contribution margin
- 航线可持续性
- 风险和不确定性
- 每条路线最大/最小可投预算
- 航司或机场的实际运营限制

最后希望输出：

- 哪些路线应该加投
- 哪些路线维持即可
- 哪些路线不建议靠营销硬救
- 不同预算场景下怎么分配

## 必须先理解的基础知识

### 1. Observed demand 不等于真实 demand

看到某条航线乘客少，不一定代表没人想飞。可能是：

- 航班太少
- 时间不好
- 价格太高
- 航线已经被削减
- 乘客被 YYZ/YVR 这类大机场吸走

所以我们要把 demand 和 supply 分开看。

### 2. MMM 不是因果魔法

MMM 可以帮助估计 marketing 和 outcome 的关系，但它依赖 aggregated data，很容易受混杂因素影响。

如果没有真实 spend 或实验校准，MMM 结果只能作为情景模拟，不能当成严格因果结论。

### 3. Adstock

本月广告不一定只影响本月，它可能影响下个月和之后几个月。

直觉：

```text
本月有效营销压力 = 本月投放 + 上月残留影响
```

### 4. Saturation

营销不是线性增长。刚开始投钱可能很有效，但投到一定程度后，边际收益会下降。

### 5. Incrementality

我们真正关心的不是总乘客，而是：

> 如果不投这笔营销预算，会少多少乘客？

这个差值才是 incremental lift。

### 6. Optimization 需要目标函数

预算优化之前，必须先定义目标。

可能目标：

- 最大化增量乘客
- 最大化利润
- 最大化 route sustainability score
- 最大化 ROI

我建议主目标用：

> 在预算和风险约束下，最大化预期增量 contribution 或 route sustainability。

### 7. 实验验证

模型给建议，实验给可信度。

最现实的实验是：

- matched-route test
- geo lift
- difference-in-differences
- synthetic control

Switchback 不太适合这个项目，因为航线营销和旅行预订窗口通常比较长。

## 我们下一步要做什么

第一步不是建模，而是做数据可行性验证：

1. 确认哪些机场和航线进入 MVP
2. 确认 outcome 用真实 passenger count 还是 route activity proxy
3. 下载或整理公开数据源
4. 搭建 route-month panel schema
5. 先做 EDA，再开始 baseline model

## 当前推荐 MVP 范围

机场可以先聚焦：

- YKF Waterloo
- YHM Hamilton
- YXU London
- YXX Abbotsford
- YLW Kelowna
- YVR Vancouver
- YYZ Toronto Pearson, 作为竞争 hub/context

路线不要一开始做太多。先选 10-20 条候选 route，确认数据能跑通，再扩展。
