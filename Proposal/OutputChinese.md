
**推荐方案**
1. 内部分析语言固定英文
2. 用户展示语言可选英文 / 中文
3. 最终报告、决策、各 section 按需翻译
4. 翻译结果缓存，避免重复耗 token

这样改动最小，稳定性最好，成本也最低。

如果你直接让所有 analyst、researcher、risk manager 都切中文：
- 每个 prompt 都要改
- 每个 agent 的辩论也会变中文
- 中间状态和历史都会变长
- 更容易影响既有 prompt 表现

所以更推荐：

- 分析语言：English
- 展示语言：English 或 中文
- 只有用户看到的结果做翻译

---

**你这个项目里应该放语言选择的层级**

### 1. 请求层
在 models.py 的 AnalysisRequest 增加两个字段：

- output_language
- translation_mode

建议值：

- output_language: en / zh
- translation_mode: none / final_only / sections / full_stream

推荐默认：
- output_language = en
- translation_mode = final_only

含义：

- none
  不翻译，全部英文
- final_only
  只翻译最终 decision 和 complete_report
- sections
  每个 section 完成后翻译一次
- full_stream
  SSE 中 agent message 也翻译，不建议默认开，最费 token

---

### 2. 前端选择层
在 types.ts 的 WizardState 增加：

- output_language: "en" | "zh"
- translation_mode: "none" | "final_only" | "sections"

然后在 +page.svelte 的配置向导加一个步骤或一个附加选项：

- Display Language
  - English
  - 中文
- Translation Scope
  - Final result only
  - Each report section
  - Raw English only

前端上这是最自然的入口。

---

### 3. 后端任务层
在 jobs.py 里，当前 complete 事件只有：

- decision
- complete_report

你应该扩展成双语结构，比如：

- decision_en
- decision_zh
- complete_report_en
- complete_report_zh

或者更通用一点：

- decision: { en, zh }
- complete_report: { en, zh }

同样，section 更新事件也可以扩展为：

- content
- translated_content
- language

但如果你先做最小版本，只在 complete 阶段翻译，就不需要改流式 section 结构。

---

## 两种实现路径

### 路径 A：只翻译最终结果
这是最推荐的第一版。

**流程**
1. 整个图保持现在英文运行
2. final_state 生成后，得到英文的 decision 和 complete_report
3. 如果用户选择中文，就调用一个轻量翻译器
4. 返回：
   - 英文原文
   - 中文译文
5. 前端根据用户选择显示其中一个

**优点**
- 改动最小
- 对现有 agent prompt 几乎零侵入
- token 增量最小
- 风险最低

**落点**
- jobs.py
- models.py
- main.py
- types.ts
- +page.svelte

---

### 路径 B：每个 section 完成后就翻译
适合你希望用户在分析过程中就能看到中文 section。

**流程**
1. analyst 输出 market_report / news_report 等英文 section
2. 在 jobs.py 的 _emit_report 时检测用户语言
3. 如果是中文，调用翻译器生成中文 section
4. SSE 推送：
   - 原文英文
   - 中文版 section

**优点**
- WebUI 体验更好
- 用户不用等最终报告

**缺点**
- 每个 section 都多一次 LLM 调用
- token 成本明显 higher
- SSE 事件模型要一起扩展

---

### 路径 C：所有 agent 直接按用户语言输出
不建议第一版就做。

你要改的地方非常多：
- market_analyst.py
- news_analyst.py
- social_media_analyst.py
- fundamentals_analyst.py
- bull_researcher.py
- bear_researcher.py
- research_manager.py
- trader.py
- aggressive_debator.py
- conservative_debator.py
- neutral_debator.py
- portfolio_manager.py

还要把 output_language 加进状态：
- agent_states.py
- propagation.py

这个方向可以做，但不适合作为第一步。

---

## 我建议的最终架构

### 第一阶段
只做“最终结果双语”

输出结构：
- canonical_language = en
- display_language = 用户选择
- decision_en
- decision_zh
- complete_report_en
- complete_report_zh

### 第二阶段
增加“section 级双语”

输出结构：
- market_report: { en, zh }
- sentiment_report: { en, zh }
- news_report: { en, zh }
- fundamentals_report: { en, zh }
- investment_plan: { en, zh }
- trader_investment_plan: { en, zh }
- final_trade_decision: { en, zh }

### 第三阶段
如果确实需要，再支持“原生中文分析”

那时再把 output_language 透传到 graph state。

---

## 翻译器应该怎么做

不要把翻译逻辑塞到每个 agent prompt 里。  
应该单独做一个 Translation Service。

建议新增一个独立模块，例如：
- webui/backend/translator.py

职责：
- translate_text(text, target_language)
- translate_sections(sections, target_language)
- 缓存相同文本的翻译结果

翻译 prompt 建议非常短，只做忠实翻译，不做改写。例如：

- 保留 Markdown 结构
- 保留 Buy / Hold / Sell 等评级词原义
- 保留 ticker、日期、表格
- 不新增结论，不删减事实

这样翻译调用会稳定很多。

---

## CLI 也可以支持双语

如果你不只关心 WebUI，而是整个系统都想支持中文查看，可以在 main.py 的用户配置流程也加一个语言选择。

CLI 最省事的方式同样是：
- 运行仍然英文
- 最后显示 complete_report 前，如果用户选中文，则翻译后再展示
- 保存磁盘时可同时输出：
  - complete_report.en.md
  - complete_report.zh.md

这样不会扰动 graph 主流程。

---

## 结合你当前代码的最小改法

### 后端
1. 在 models.py 增加 output_language 和 translation_mode
2. 在 main.py 保持透传即可
3. 在 jobs.py 的 _run_analysis 末尾：
   - 先得到英文 complete_report
   - 如果 output_language 是 zh，就翻译
   - complete 事件里返回双语字段

### 前端
1. 在 types.ts 增加语言字段
2. 在 +page.svelte 增加语言选择 UI
3. 分析结果页根据用户选择显示英文或中文

---

## 成本和效果对比

### 方案 1：最终结果翻译
- 成本：低
- 改动：低
- 风险：低
- 推荐度：最高

### 方案 2：section 级翻译
- 成本：中
- 改动：中
- 风险：中
- 推荐度：第二阶段

### 方案 3：所有 agent 原生中文
- 成本：高
- 改动：高
- 风险：高
- 推荐度：最后再做

---

## 我给你的直接建议

如果你的目标是“让使用者能选英文还是中文”，最合理的是：

1. 内部分析统一英文
2. WebUI 增加语言选择
3. 默认只翻译 final report 和 decision
4. 后续再扩展到 section 级双语
5. 不要第一版就改所有 agent prompt

这样你能最快上线，而且不会把现有分析链路搞乱。

如果你要，我下一步可以继续直接给你一版“具体改动清单”，精确到：
- AnalysisRequest 新增哪些字段
- jobs.py 的 complete 事件该改成什么结构
- 前端下拉框该放在哪一步
- translator.py 的接口长什么样