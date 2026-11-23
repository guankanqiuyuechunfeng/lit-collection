# -*- coding: utf-8 -*-
"""
生成最终五件套交付物：
  index.html                      可交互网页清单（搜索 / 方向筛选 / 档次筛选 / 排序 / 导出 CSV）
  <topic>_文献检索报告.md          中文报告（分方向表格 + 每篇要点 + 趋势观察）
  文献清单.csv                     全字段表格（Excel 可直接打开）
  references.ris / references.bib  导入 EndNote / Zotero / LaTeX

用法：
    python build.py --config config.json --notes notes.json [--verified verified.json]

notes.json 结构（由 WorkBuddy 撰写，见 references/workflow.md）：
  {"notes": {"10.xxxx/yyy": {"cn": "中文译名", "note": "一句话要点"}},
   "trends": ["趋势判断1", "趋势判断2"]}
"""
import argparse
import csv
import datetime
import html as H
import json
import os
import re

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
TIER_LABEL = {"A": "A档", "C": "国内主办", "B": "补充档"}
TIER_ORDER = {"A": 0, "C": 1, "B": 2}


def clean(s):
    if not s:
        return ""
    return WS.sub(" ", TAG.sub(" ", H.unescape(str(s)))).strip()


def safe_filename(s):
    return re.sub(r'[\\/:*?"<>|]', "_", s).strip() or "文献"


def load_notes(path):
    if not path or not os.path.exists(path):
        return {}, []
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    if "notes" in d:
        return d["notes"], d.get("trends", [])
    flat = {k: v for k, v in d.items() if k not in ("trends", "summary", "method_note")}
    return flat, d.get("trends", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--notes", default="notes.json")
    ap.add_argument("--verified", default="verified.json")
    ap.add_argument("--template", default=None,
                    help="HTML 模板路径，默认取 skill 的 assets/template.html")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    with open(args.verified, encoding="utf-8") as f:
        data = json.load(f)
    notes, trends = load_notes(args.notes)

    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tpl_path = args.template or os.path.join(skill_dir, "assets", "template.html")
    with open(tpl_path, encoding="utf-8") as f:
        tpl = f.read()

    out_dir = cfg.get("output_dir", ".")
    os.makedirs(out_dir, exist_ok=True)
    topic = cfg.get("topic") or cfg.get("title") or "文献"
    title = cfg.get("title") or (topic + " —— 高影响力文献清单")
    date_str = cfg.get("date") or datetime.date.today().isoformat()
    y0, y1 = int(cfg["year_from"]), int(cfg["year_to"])
    if_year = cfg.get("if_year", "2024")
    cat_names = [c["name"] for c in cfg["categories"]]

    # ---------- 统一整理 ----------
    rows = []
    for r in data:
        n = notes.get(r["doi"], {}) or {}
        if isinstance(n, str):
            n = {"cn": n, "note": ""}
        t = clean(r.get("title_official") or r.get("cr_title") or r.get("title"))
        j = clean(r.get("journal_official") or r.get("cr_journal") or r.get("journal"))
        au = [clean(a) for a in (r.get("cr_authors") or r.get("authors") or [])]
        rows.append({
            "doi": r["doi"], "t": t, "j": j,
            "y": r.get("cr_year") or r.get("year"),
            "if": r.get("if") or 0, "c": r.get("cited_by") or 0,
            "au": ", ".join(au[:3]) + (", et al." if len(au) > 3 else ""),
            "authors": au,
            "cn": n.get("cn", ""), "note": n.get("note", ""),
            "cat": r.get("cat") or (r.get("cats") or ["通用"])[0],
            "tier": r.get("tier", "A"),
            "vol": r.get("cr_volume"), "iss": r.get("cr_issue"),
            "page": r.get("cr_page"),
            "abstract": clean(r.get("abstract") or "")[:900],
            "verify": r.get("verify", ""),
        })

    n_ver = sum(1 for r in rows if r["verify"] == "verified")
    n_mis = sum(1 for r in rows if r["verify"].startswith("mismatch"))
    n_nf = sum(1 for r in rows if r["verify"] == "not_found")

    # ---------- 1. index.html ----------
    payload = []
    for r in sorted(rows, key=lambda x: (cat_names.index(x["cat"]) if x["cat"] in cat_names else 99,
                                         TIER_ORDER.get(x["tier"], 3), -x["if"])):
        payload.append({
            "cat": r["cat"] + "·" + TIER_LABEL.get(r["tier"], ""),
            "cn": r["cn"], "t": r["t"], "j": r["j"], "y": r["y"],
            "if": r["if"], "c": r["c"], "au": r["au"],
            "note": r["note"], "doi": r["doi"],
        })
    cat_opts = "".join(f"<option>{H.escape(c)}</option>" for c in cat_names)
    if_th = cfg.get("if_threshold", 5)
    tier_opts = ('<option value="A档">A档 (IF≥' + str(if_th) + ')</option>'
                 '<option value="国内主办">国内主办</option>'
                 '<option value="补充档">补充档 (IF&lt;5)</option>')
    footer = (f"数据源：OpenAlex + Crossref"
              + ("（含国内主办期刊 ISSN 定向检索）" if cfg.get("cn_issns") else "")
              + f"。共 {len(rows)} 篇，{n_ver} 条元数据完全一致，{n_mis} 条为在线优先/正式刊期年份或题名标记差异"
              + (f"，{n_nf} 条 DOI 未在 Crossref 命中" if n_nf else "") + "。")
    html_out = (tpl.replace("__DOC_TITLE__", H.escape(title))
                   .replace("__TITLE__", H.escape(title))
                   .replace("__DATE__", date_str)
                   .replace("__YEAR_RANGE__", f"{y0}–{y1}")
                   .replace("__IF_YEAR__", str(if_year))
                   .replace("__CAT_OPTIONS__", cat_opts)
                   .replace("__TIER_OPTIONS__", tier_opts)
                   .replace("__FOOTER__", H.escape(footer))
                   .replace("__CSV_NAME__", "文献清单.csv")
                   .replace("__DATA__", json.dumps(payload, ensure_ascii=False)))
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_out)

    # ---------- 2. Markdown 报告 ----------
    L = []
    A = L.append
    A(f"# {title}\n")
    A(f"> 检索日期：{date_str} 　|　时间范围：{y0}–{y1} 　|　数据源：OpenAlex、Crossref"
      + ("（含国内主办期刊定向检索）" if cfg.get("cn_issns") else ""))
    A(f"> 入选文献 **{len(rows)} 篇**，全部 DOI 经 Crossref 逐条核验"
      f"（{n_ver} 条完全一致，{n_mis} 条为在线优先/正式刊期年份或题名标记差异"
      + (f"，{n_nf} 条未在 Crossref 命中" if n_nf else "") + "）。\n")
    A("## 一、检索与筛选方法\n")
    A("| 环节 | 说明 |")
    A("|---|---|")
    n_q = sum(len(c["queries"]) for c in cfg["categories"])
    A("| 数据源 | OpenAlex（综合学术索引）+ Crossref（出版商权威元数据）"
      + ("；国内主办期刊按 ISSN 定向检索" if cfg.get("cn_issns") else "") + " |")
    A(f"| 检索式 | {n_q} 组主题词，覆盖 " + "、".join(cat_names) + " 等方向，每组按相关度与被引双路排序 |")
    A(f"| 时间过滤 | {y0}-01-01 至 {y1}-12-31 |")
    A(f"| 相关性打分 | 题名/摘要关键词加权（强相关词权重 6，弱相关词 0.5–2），阈值 ≥{cfg.get('rel_min', 8)} |")
    A("| 影响力打分 | 期刊影响因子 + 年均被引速率 + 时效性加权，同刊最多取 3 篇以保证多样性 |")
    A(f"| 分级 | **A 档**：IF ≥ {cfg.get('if_threshold', 5)}；**国内主办**：国内主办高水平期刊；**补充档**：IF < {cfg.get('if_threshold', 5)} 的领域权威刊 |")
    A("| 核验 | 逐条比对 Crossref 的题名、期刊、年份；导出 RIS / BibTeX / CSV |")
    A("")
    A(f"> ⚠️ 表中 IF 为 **{if_year} JCR 近似参考值**，仅用于排序与筛选，正式引用请以 JCR 官方数据为准；"
      "被引数为检索时点的 OpenAlex / Crossref 记录值。\n")
    A("## 二、清单总览\n")
    A("| 方向 | 篇数 |")
    A("|---|---|")
    for c in cat_names:
        A(f"| {c} | {sum(1 for r in rows if r['cat'] == c)} |")
    A(f"| **合计** | **{len(rows)}** |")
    A("")
    for idx, c in enumerate(cat_names, 1):
        items = [r for r in rows if r["cat"] == c]
        A(f"## 三.{idx} {c}\n")
        for tier in ("A", "C", "B"):
            grp = sorted([r for r in items if r["tier"] == tier], key=lambda x: -x["if"])
            if not grp:
                continue
            label = {"A": "A 档 · 高影响因子主榜",
                     "C": "国内主办高水平期刊",
                     "B": "补充档 · 领域权威期刊"}[tier]
            A(f"### {label}（{len(grp)} 篇）\n")
            A("| # | 中文译名 | 原题 | 期刊 | 年 | IF≈ | 被引 | DOI |")
            A("|---|---|---|---|---|---|---|---|")
            for i, r in enumerate(grp, 1):
                A(f"| {i} | **{r['cn'] or '—'}** | {r['t']} | {r['j']} | {r['y']} | "
                  f"{r['if']} | {r['c']} | [{r['doi']}](https://doi.org/{r['doi']}) |")
            A("")
            A("**要点速览**\n")
            for i, r in enumerate(grp, 1):
                A(f"- **{i}. {r['cn'] or r['t']}**（{r['j']}, {r['y']}）：{r['note'] or '（待补充要点）'}")
            A("")
    if trends:
        A("## 四、研究热点与选题观察\n")
        for i, t in enumerate(trends, 1):
            A(f"{i}. {t}")
        A("")
    A("## 五、配套文件\n")
    A("| 文件 | 用途 |")
    A("|---|---|")
    A("| `index.html` | 带搜索、方向/档次筛选与排序的网页版清单，可导出 CSV |")
    A("| `references.ris` | 可直接导入 EndNote / NoteExpress / Zotero |")
    A("| `references.bib` | BibTeX，配合 LaTeX 使用 |")
    A("| `文献清单.csv` | Excel 可打开的全字段清单表 |")
    A("")
    A("---\n")
    A("*说明：本报告基于公开学术数据库元数据自动生成与人工审校；CNKI、万方、Web of Science、Scopus "
      "等未被上述接口收录的文献未纳入。如需补充纯中文期刊，请另行指定检索途径。*")
    report_name = safe_filename(topic) + "_文献检索报告.md"
    with open(os.path.join(out_dir, report_name), "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    # ---------- 3. CSV ----------
    rows_sorted = sorted(rows, key=lambda r: (
        cat_names.index(r["cat"]) if r["cat"] in cat_names else 99,
        TIER_ORDER.get(r["tier"], 3), -(r["if"] or 0)))
    with open(os.path.join(out_dir, "文献清单.csv"), "w",
              encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["方向", "档次", "中文译名", "中文要点", "原题", "期刊", "年份",
                    "影响因子(参考)", "被引", "作者", "卷", "期", "页码", "DOI", "链接"])
        for r in rows_sorted:
            w.writerow([r["cat"], TIER_LABEL.get(r["tier"], ""), r["cn"], r["note"],
                        r["t"], r["j"], r["y"], r["if"], r["c"], "; ".join(r["authors"]),
                        r["vol"] or "", r["iss"] or "", r["page"] or "",
                        r["doi"], f"https://doi.org/{r['doi']}"])

    # ---------- 4. RIS ----------
    with open(os.path.join(out_dir, "references.ris"), "w", encoding="utf-8") as f:
        for r in rows_sorted:
            f.write("TY  - JOUR\n")
            for a in r["authors"]:
                f.write(f"AU  - {a}\n")
            f.write(f"TI  - {r['t']}\nJO  - {r['j']}\nJF  - {r['j']}\n")
            f.write(f"PY  - {r['y']}\nDA  - {r['y']}///\n")
            if r["vol"]:
                f.write(f"VL  - {r['vol']}\n")
            if r["iss"]:
                f.write(f"IS  - {r['iss']}\n")
            if r["page"]:
                f.write(f"SP  - {r['page']}\n")
            f.write(f"DO  - {r['doi']}\nUR  - https://doi.org/{r['doi']}\n")
            if r["cn"]:
                f.write(f"KW  - {r['cn']}\n")
            f.write(f"KW  - {r['cat']}\n")
            if r["note"]:
                f.write(f"N1  - {r['note']}\n")
            if r["abstract"]:
                f.write(f"AB  - {r['abstract']}\n")
            f.write("ER  - \n\n")

    # ---------- 5. BibTeX ----------
    def citekey(r):
        last = (r["authors"][0].split()[-1] if r["authors"] else "anon")
        last = re.sub(r"[^A-Za-z]", "", last) or "anon"
        return f"{last}{r['y']}{re.sub(r'[^A-Za-z0-9]', '', r['t'][:10]).lower()}"

    with open(os.path.join(out_dir, "references.bib"), "w", encoding="utf-8") as f:
        for r in rows_sorted:
            f.write(f"@article{{{citekey(r)},\n")
            f.write(f"  title   = {{{r['t']}}},\n")
            f.write(f"  author  = {{{' and '.join(r['authors'])}}},\n")
            f.write(f"  journal = {{{r['j']}}},\n")
            f.write(f"  year    = {{{r['y']}}},\n")
            if r["vol"]:
                f.write(f"  volume  = {{{r['vol']}}},\n")
            if r["iss"]:
                f.write(f"  number  = {{{r['iss']}}},\n")
            if r["page"]:
                f.write(f"  pages   = {{{r['page']}}},\n")
            f.write(f"  doi     = {{{r['doi']}}},\n")
            f.write(f"  note    = {{{r['cn'] + '；' if r['cn'] else ''}{r['note']}}},\n")
            f.write("}\n\n")

    print(f"built {len(rows)} records -> {os.path.abspath(out_dir)}")
    print(f"  index.html / {report_name} / 文献清单.csv / references.ris / references.bib")


if __name__ == "__main__":
    main()
