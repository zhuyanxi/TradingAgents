
**先给结论（按收益排序）**
1. 做中间层摘要总线（Summary Bus），不要把四份长报告反复喂给后续所有角色。  
2. 把辩论历史从“全文累加”改成“滑动窗口 + 滚动摘要”。  
3. 工具输出结构化压缩（CSV/新闻先压缩再进 LLM）。  
4. 去掉最后一次“只为提取评级”的额外 LLM 调用。  
5. 增加节点级 token 预算治理（超预算自动降级）。

---

## 你当前最耗 token 的点（代码证据）

1. 多个角色都在拼接四份完整报告作为上下文  
bull_researcher.py  
bear_researcher.py  
research_manager.py  
trader.py  
portfolio_manager.py

2. 辩论历史是字符串持续追加，轮次越多输入越大  
bull_researcher.py  
bear_researcher.py  
aggressive_debator.py  
conservative_debator.py  
neutral_debator.py

3. 工具返回原始长文本/CSV，直接进入模型上下文  
y_finance.py  
y_finance.py  
yfinance_news.py

4. 最终信号提取还要再调用一次模型  
signal_processing.py  
trading_graph.py

---

## 架构优化方案（可落地）

### P0：摘要总线（预期省 35%-55%）
- 在四个 Analyst 输出后，新增一个轻量节点生成结构化摘要：
- 字段建议：thesis, key_facts, risks, confidence, evidence
- 每份摘要限制 200-400 tokens
- 后续 Bull/Bear/Trader/Manager 只读摘要，原文只用于最终展示和存档

落点：插入到 graph analyst 阶段后，接在 setup.py 的分析链路之后。

### P0：辩论上下文改“滑动窗口 + 滚动摘要”（预期省 25%-45%）
- 保留 recent_turns（最近 2-3 轮原文）
- 历史长文本压缩到 debate_summary（固定 300-500 tokens）
- 每轮输入：debate_summary + recent_turns + 对方上一条
- 不再使用全文 history 直接累加

当前轮次控制在 conditional_logic.py 和 conditional_logic.py，你可以保留轮次逻辑，仅替换上下文载荷。

### P0：工具输出压缩层（预期省 20%-40%）
- 在 tool 层加“标准化返回格式”，避免把完整 CSV/整段新闻送进模型
- 股票数据：仅保留最近 N 条 + 统计特征（收益率、波动率、区间高低）
- 财报：仅保留关键指标列和最近 4 个 period
- 新闻：去重后 top-k，保留 title/date/source/sentiment，不传全文

入口可放在 interface.py 的路由后统一处理。

### P1：去掉最终评级提取 LLM 调用（预期省 3%-8%）
- 现在是模型读完整 final_trade_decision 再抽一个词
- 用规则解析即可（Buy/Overweight/Hold/Underweight/Sell）
- 仅在规则失败时 fallback 到 LLM

替换点：signal_processing.py

### P1：节点级 token 预算治理（预期省 10%-25%）
- 你已经有全局统计器 stats_handler.py
- 增加 per-node 预算，例如：
- Analyst 总预算
- Research Debate 总预算
- Risk Debate 总预算
- 超预算策略：降级模型、缩短输出、提前收敛到 Manager

---

## 额外高价值建议（SaaS 视角）

1. 请求级缓存
- 键：ticker + date + selected_analysts + provider + model + vendor
- Tool 和中间摘要都可缓存，重复请求几乎零增量 token

2. Prompt 模板瘦身
- 现在多个 agent 的 system prompt 很长且重复
- 抽成共享短模板 + 任务差异参数，减少每次输入固定成本

3. 输出长度硬限制
- 在客户端层统一注入 max tokens / output budget
- 特别是 quick model 节点，避免“过度写作”

---

## 推荐改造顺序（最快见效）

1. 摘要总线  
2. 辩论窗口化  
3. 工具输出压缩  
4. 去掉 signal extractor 的 LLM 调用  
5. 节点预算治理 + 缓存

如果你愿意，我下一步可以直接给你一版“最小改造设计稿”（包含新增 state 字段、graph 节点插入位置、每个节点的输入输出 schema），你可以按这个在 1-2 天内落地第一版。