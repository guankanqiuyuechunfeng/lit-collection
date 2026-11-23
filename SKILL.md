---
name: lit-collection
description: 按用户指定主题检索、筛选并整理成一套可交付的文献合集（可交互网页清单 + 中文报告 + CSV + RIS/BibTeX）。当用户说「整理文献」「文献整理」「帮我整理 XX 方向的文献」「找一批文献并做成合集」，或要求近 N 年、高影响因子、国内外文献清单、带搜索筛选的文献网页时，应使用本 skill。输出形态与工作区已有的 index.html / 文献检索报告 / 文献清单.csv / references.ris / references.bib 一致。
agent_created: true
---

# 文献整理合集（lit-collection）

## Overview

把一个自然语言文献需求（主题、年份、影响力要求、国内外范围、篇数）转成**五件套交付物**：

| 文件 | 内容 |
|---|---|
| `index.html` | 可交互网页清单：关键词搜索、方向/档次筛选、按 IF/被引/年份排序、一键导出 CSV |
| `<topic>_文献检索报告.md` | 中文报告：检索与筛选方法、分方向表格、每篇中文译名与要点、研究热点观察 |
| `文献清单.csv` | 全字段表格，Excel 可直接打开 |
| `references.ris` | 导入 EndNote / NoteExpress / Zotero |
| `references.bib` | BibTeX，供 LaTeX 使用 |

底层走公开学术 API（OpenAlex + Crossref），DOI 逐条经 Crossref 核验；**不写死任何主题**，方向、检索式、年份、篇数全部由本次需求生成的 `config.json` 决定。

## 触发与范围

- 触发词：「整理文献」及同类表述（见 frontmatter description）。
- 适用场景：某个研究方向的文献调研、开题/综述前的文献摸底、需要可筛选网页清单与参考文献导入文件的场合。
- 不适用：单篇文献的翻译与精读（用 PDF 相关 skill）；纯 CNKI/万方中文期刊检索（本链路覆盖不到，见限制）。

## 工作流

先在当前工作区建运行目录 `litwork/`，把 `<skill_dir>` 记为本 skill 的根目录。用同一个 Python 解释器执行所有脚本。

### Step 1 — 根据需求写 `litwork/config.json`

以 `references/config_example.json` 为模板，把用户的自然语言要求翻译成配置：

- 拆 `categories`：多子方向需求各建一个 category；单一主题可拆成「材料设计 / 机理 / 应用」等互补视角。
- 定 `year_from` / `year_to`：默认最近 5 年；用户说「近三年」等则相应收窄。
- 写 `queries`：每个方向 5–10 组**英文**短语，覆盖核心术语、主流材料体系、工艺、性能指标、应用场景、综述。
- 写 `strong` / `weak` 词表：强相关词用高区分度术语，弱相关词用跨方向宽泛词；一律小写、用词干片段（如 `lubricat`）。**词表质量直接决定归类与排序质量**。
- 按「尽量多 / 精选」调 `per_cat_high`、`per_cat_low`、`cn_pick`；允许国内外文献时填 `cn_issns`。
- `output_dir` 填 `..`，让五件套落到工作区根目录。

字段定义与「需求 → 配置」转换细则见 `references/workflow.md` §2–§3。

### Step 2 — 检索

```bash
cd <工作区>/litwork
python <skill_dir>/scripts/harvest.py --config config.json --out raw.jsonl
```

耗时最长，用后台任务运行并等待完成。OpenAlex + Crossref 双源、增量落盘、带指数退避。若 OpenAlex 大面积 429，把 `use_openalex` 设为 `false` 后重跑（Crossref 单源即可完成）。

### Step 3 — 筛选与核验

```bash
python <skill_dir>/scripts/select.py  --config config.json --raw raw.jsonl --out selected.json
python <skill_dir>/scripts/verify.py  --in selected.json --out verified.json --workers 3
```

按 DOI 去重 → 相关性/影响力打分 → 分 A/B/C 档（同刊限篇保证多样性）→ Crossref 逐条核验并补全权威元数据。若入选篇数明显偏少，把 `rel_min` 从 8 降到 5–6 后重跑 Step 3。

### Step 4 — 撰写中文要点（**必须由 WorkBuddy 完成，不可跳过**）

```bash
python <skill_dir>/scripts/notes_input.py --verified verified.json --out notes_input.md
```

读 `notes_input.md`，为**每一篇**入选文献写中文译名 `cn` 与一句话要点 `note`，并归纳 3–5 条 `trends`，写入 `litwork/notes.json`。格式与撰写规范见 `references/workflow.md` §4。要点要引用摘要中的具体机制或数据，避免空泛套话。

### Step 5 — 生成交付物并呈现

```bash
python <skill_dir>/scripts/build.py --config config.json --notes notes.json --verified verified.json
```

按 `references/workflow.md` §6 做质量核查，然后用 `present_files` 一次性呈现 5 个文件，`index.html` 放第一位。

### Step 6 — 收尾说明

在最终回复里概括检索规模、各方向篇数、几个高价值条目与热点判断，并**明确说明两条限制**：IF 为 2024 JCR 近似参考值（正式引用以 JCR 官方为准）；CNKI/万方独有的纯中文期刊未被 Crossref 收录、默认未纳入，需要时可另换途径补检。

## 关键约定

- **配置驱动，不硬编码主题**：任何主题都通过 `config.json` 传入；脚本与模板保持通用。
- **真实检索**：必须实际调用公开 API 抓取，不得凭记忆编造文献清单或 DOI。
- **必须核验**：交付前每篇 DOI 都要经 Crossref 比对；核验不一致要在页脚与回复中说明。
- **必须写中文要点**：`notes.json` 是本 skill 的价值核心，缺了它网页与报告只是英文元数据罗列。
- **五件套齐全**：不要只交 `index.html`。
- **HTML 模板不再手写**：`build.py` 自动读取 `assets/template.html` 渲染；模板已内置 HTML 转义，勿在 JSON 数据里塞未转义的标签。

## 资源

| 路径 | 用途 |
|---|---|
| `references/workflow.md` | 完整命令、config 字段表、需求转配置指南、notes 规范、限流降级、质量核查、已知限制 |
| `references/config_example.json` | 可直接改写的完整配置示例（耐磨/减磨/摩阻三方向） |
| `scripts/harvest.py` | OpenAlex + Crossref 双源检索，增量落盘、退避重试 |
| `scripts/select.py` | 去重、相关性/影响力打分、A/B/C 分级 |
| `scripts/verify.py` | Crossref DOI 核验与权威元数据补全 |
| `scripts/notes_input.py` | 导出待撰写中文要点清单 |
| `scripts/build.py` | 生成 index.html / 报告 / CSV / RIS / BibTeX |
| `scripts/journal_if.py` | 期刊影响因子近似参考表（精确匹配，避免同名词串误配） |
| `assets/template.html` | 可交互网页模板（搜索 / 筛选 / 排序 / 导出 CSV） |
