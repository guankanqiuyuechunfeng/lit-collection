# 文献整理合集：完整工作流程

本文件是 `lit-collection` skill 的详细执行参考。SKILL.md 给出主干，本文件给出命令、参数与坑位。

## 0. 目录约定

在**当前工作区**下建一个运行目录（例如 `litwork/`），所有中间文件都放这里，最终交付物由 `config.output_dir` 指定（通常 `..`，即工作区根目录）。

```
<工作区>/
├── litwork/
│   ├── config.json          由 WorkBuddy 根据用户需求写
│   ├── raw.jsonl            检索原始记录
│   ├── raw.jsonl.done.json  已完成 job（续跑用）
│   ├── selected.json        筛选结果
│   ├── verified.json        DOI 核验后
│   ├── notes_input.md       待撰写要点清单
│   └── notes.json           由 WorkBuddy 撰写的中文译名、要点、趋势
├── index.html               ← 交付
├── <topic>_文献检索报告.md   ← 交付
├── 文献清单.csv              ← 交付
├── references.ris            ← 交付
└── references.bib            ← 交付
```

所有脚本用同一个 Python 解释器执行，Windows 上路径为
`C:/Users/张富祥/.workbuddy/binaries/python/versions/3.13.12/python.exe`。
脚本位于 `<skill_dir>/scripts/`，模板位于 `<skill_dir>/assets/template.html`（build.py 会自动定位）。

## 1. 五步命令

```bash
cd <工作区>/litwork

# 1) 检索（耗时最长，建议后台运行）
python <skill_dir>/scripts/harvest.py --config config.json --out raw.jsonl

# 2) 去重 + 打分 + 分级
python <skill_dir>/scripts/select.py --config config.json --raw raw.jsonl --out selected.json

# 3) Crossref 逐条 DOI 核验（补全题名/期刊/年份/卷期页/作者）
python <skill_dir>/scripts/verify.py --in selected.json --out verified.json --workers 3

# 4) 导出待撰写清单 → 由 WorkBuddy 撰写 notes.json
python <skill_dir>/scripts/notes_input.py --verified verified.json --out notes_input.md

# 5) 生成五件套交付物
python <skill_dir>/scripts/build.py --config config.json --notes notes.json --verified verified.json
```

第 1 步和第 3 步需要联网。若网络受限，见 §5 降级方案。

## 2. config.json 字段

完整示例见 `references/config_example.json`。

| 字段 | 必填 | 说明 |
|---|---|---|
| `title` | 是 | 网页 `<h1>` 与报告标题 |
| `topic` | 是 | 用于报告文件名，如 `耐磨减磨摩阻材料` |
| `year_from` / `year_to` | 是 | 年份范围（整数） |
| `if_year` | 否 | IF 参考年份，默认 `2024` |
| `if_threshold` | 否 | A 档 IF 阈值，默认 `5.0` |
| `rel_min` | 否 | 相关性入选阈值，默认 `8`；结果太少可降到 `5–6` |
| `per_cat_high` | 否 | 每个方向 A 档最多篇数，默认 `18` |
| `per_cat_low` | 否 | 每个方向补充档最多篇数，默认 `8` |
| `cn_pick` | 否 | 国内主办期刊补充篇数，默认 `12` |
| `cn_issns` | 否 | 国内主办期刊 ISSN 列表；留空或省略则跳过 C 档 |
| `use_openalex` | 否 | 默认 `true`；设为 `false` 只跑 Crossref（更快、更稳） |
| `output_dir` | 否 | 交付物输出目录，默认 `.`；填 `..` 输出到工作区根目录 |
| `mailto` | 否 | OpenAlex/Crossref 的礼貌池标识 |
| `categories` | 是 | 方向数组，见下 |

每个 `category`：

| 字段 | 说明 |
|---|---|
| `name` | 中文方向名（用于网页下拉、报告分节、表格分组） |
| `queries` | 英文检索式数组，每组会按相关度 + 被引两路排序检索；建议每方向 5–10 组 |
| `strong` | 强相关关键词（题名命中 +6，摘要命中 +2） |
| `weak` | 弱相关关键词（题名命中 +2，摘要命中 +0.5） |

**关键**：`strong`/`weak` 决定归类与排序质量，必须小写、用英文词干片段（如 `lubricat` 能同时命中 lubricate / lubrication / lubricant）。

## 3. 把用户要求转成 config（最重要的一步）

用户说「整理文献，帮我找 XXX 方向近五年高影响力文献」时：

1. **拆方向**：若需求含多个子方向（如"耐磨、减磨、摩阻"），每个子方向一个 category；若为单一主题，可拆成 2–3 个互补视角（如"材料设计 / 机理 / 应用"）以丰富清单。
2. **定年份**：默认最近 5 年（当前年份减 4 到当前年份）；用户明确说"近三年"则相应收窄。
3. **写检索式**：每个方向 5–10 组**英文**短语，覆盖：核心术语、主流材料体系、制备工艺、性能指标、应用场景、综述。避免过长句子（OpenAlex/Crossref 对长查询召回差）。
4. **写词表**：`strong` 用该方向独有的高区分度词；`weak` 用跨方向共有的宽泛词。不要把所有词都放进 `strong`，否则所有文献都高分、失去区分度。
5. **定篇数**：用户说"尽量多"→ `per_cat_high` 20–25、`cn_pick` 12–15；说"精选十几篇"→ 相应减半。
6. **国内刊**：需求允许"国内外都行"时填 `cn_issns`（示例里那 10 个是材料/摩擦学常用国内主办刊，可按主题增补）；只要国外文献则留空。

可参考 `references/config_example.json` 作为起点，替换主题词即可。

## 4. notes.json 撰写规范

第 4 步生成的 `notes_input.md` 含每篇的 DOI / 原题 / 期刊 / 年份 / 摘要片段。WorkBuddy 需逐条撰写：

```json
{
  "notes": {
    "10.1002/adma.202207757": {
      "cn": "二维 MXene 摩擦学展望",
      "note": "MXene 摩擦学顶级综述，覆盖润滑添加剂、复合材料增强相、固体润滑涂层三大方向与机理。"
    }
  },
  "trends": [
    "高熵/中熵合金 + 激光熔覆是耐磨主线。",
    "减磨研究从实现超滑转向工程耐久与绿色润滑。"
  ]
}
```

要求：

- **每条入选文献都要有条目**，键为小写 DOI；漏写的会显示原题名与"（待补充要点）"，降低交付质量。
- `cn` 为 8–20 字中文译名，不要直译原文标题，要突出研究对象与贡献。
- `note` 为**一句话**（40–80 字），说明做了什么、关键结论或为何值得读；优先引用摘要里的具体数据/机制，避免空泛的"研究了……的性能"。
- `trends` 为 3–5 条趋势判断，基于本次清单的期刊/题名分布归纳，用于报告第四节；不要照抄其他主题的趋势。
- 中文正文里用中文引号「」或“”，**不要在中文之间套英文直引号**（Python 字符串里会引发语法问题，且排版难看）。

## 5. 限流、降级与续跑

- **OpenAlex 容易 429**：harvest.py 已做指数退避（4/8/16 s）与 0.8 s 间隔。若大批失败，设置 `use_openalex: false`，仅用 Crossref 重跑（Crossref 稳定，约 1–2 分钟）。
- **增量续跑**：已完成的 job 记在 `raw.jsonl.done.json`；中断后重跑同一命令会跳过已完成项。要彻底重来，删掉 `raw.jsonl` 与 `.done.json`。
- **Crossref 也可能限流**：verify.py 并发默认 3，若报错降到 `--workers 1` 并重试。
- **OpenAlex 摘要**：由 `abstract_inverted_index` 还原；Crossref 摘要常含 JATS 标签，build.py 会清洗。Elsevier 系摘要覆盖差属正常，不影响主体。
- **DOI 查不到**：verify.py 保留记录并标 `not_found`，不丢弃；build.py 会在页脚提示数量。

## 6. 交付前质量核查

1. `index.html` 用浏览器打开，确认搜索、方向筛选、档次筛选、三种排序、导出 CSV 都正常；表格无空白行、`IF≈` 与「被引」列有数值。
2. 报告分节数量与 `categories` 一致，每节表格行数与「要点速览」条数一致。
3. `文献清单.csv` 行数 = 入选篇数；`references.ris` 的 `TY - JOUR` 条数、`references.bib` 的 `@article` 条数一致。
4. 抽查 3–5 个 DOI 链接可打开（https://doi.org/...）。
5. 用 `present_files` 一次性呈现 5 个交付文件，`index.html` 放第一位（会自动在预览面板打开）。

## 7. 已知限制（须在最终回复中说明）

- **IF 是近似参考值**：`journal_if.py` 里是 2024 JCR 人工整理的近似表，且**只做规范化后精确匹配**；未命中的期刊 IF 记 0，会落入补充档或不入选。正式引用请以 JCR 官方数据为准。
- **中文期刊覆盖不全**：CNKI/万方独有的纯中文刊（如《摩擦学学报》中文版）未被 Crossref 收录，默认不纳入；需补充时换其他途径。
- **摘要缺失**：部分出版商不向公开接口提供摘要，中文要点需依据题名与期刊推断，应在要点里避免编造具体数值。
- **分级是排序工具**：A/B/C 档仅用于组织清单，不代表学术质量的绝对评判。
