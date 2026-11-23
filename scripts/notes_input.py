# -*- coding: utf-8 -*-
"""
导出精简待撰写清单，供 WorkBuddy 为每篇文献写中文译名与一句话要点。

用法：
    python notes_input.py --verified verified.json [--out notes_input.md]

输出的每一行含 DOI / 原题 / 期刊 / 年份 / 摘要片段，便于逐条撰写 notes.json。
"""
import argparse
import json
import re

TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")
TIER_ORDER = {"A": 0, "C": 1, "B": 2}


def clean(s):
    if not s:
        return ""
    return WS.sub(" ", TAG.sub(" ", str(s))).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verified", default="verified.json")
    ap.add_argument("--out", default="notes_input.md")
    ap.add_argument("--abstract", type=int, default=320)
    args = ap.parse_args()

    with open(args.verified, encoding="utf-8") as f:
        data = json.load(f)
    data.sort(key=lambda r: (r.get("cat", ""), TIER_ORDER.get(r.get("tier"), 3),
                             -(r.get("if") or 0)))
    L = ["# 待撰写中文要点清单", "",
         f"共 {len(data)} 篇。请为每一篇写 notes.json，格式见 references/workflow.md。", ""]
    cur = None
    for i, r in enumerate(data, 1):
        key = (r.get("cat", ""), r.get("tier", ""))
        if key != cur:
            cur = key
            L += [f"## {key[0]} · {key[1]} 档", ""]
        t = clean(r.get("title_official") or r.get("cr_title") or r.get("title"))
        j = clean(r.get("journal_official") or r.get("cr_journal") or r.get("journal"))
        ab = clean(r.get("abstract") or "")[:args.abstract]
        L.append(f"**{i}. {t}**")
        L.append(f"- DOI: `{r['doi']}`")
        L.append(f"- {j}, {r.get('cr_year') or r.get('year')} | IF≈{r.get('if') or 0} | 被引 {r.get('cited_by') or 0}")
        if ab:
            L.append(f"- 摘要: {ab}")
        L.append("")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"wrote {len(data)} entries -> {args.out}")


if __name__ == "__main__":
    main()
