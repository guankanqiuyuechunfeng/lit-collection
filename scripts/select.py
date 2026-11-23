# -*- coding: utf-8 -*-
"""
去重 -> 相关性/影响力打分 -> 分主题筛选 -> 分级

用法：
    python select.py --config config.json [--raw raw.jsonl] [--out selected.json]

分级：
  A 档   IF >= if_threshold（高影响力主榜）
  B 档   0 < IF < if_threshold（领域权威补充档）
  C 档   国内主办期刊定向补充（config.cn_issns）
同刊限篇以保证期刊多样性。
"""
import argparse
import html
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from journal_if import get_if


def clean(s):
    if not s:
        return ""
    return html.unescape(str(s)).strip()


def kw_score(rec, cat_cfg):
    t = (rec.get("title") or "").lower()
    a = (rec.get("abstract") or "").lower()
    s = 0.0
    hits = []
    for k in cat_cfg.get("strong", []):
        k = k.lower()
        if k in t:
            s += 6
            hits.append(k)
        elif k in a:
            s += 2
            hits.append(k)
    for k in cat_cfg.get("weak", []):
        k = k.lower()
        if k in t:
            s += 2
        elif k in a:
            s += 0.5
    return round(s, 1), sorted(set(hits))


def load_raw(path):
    recs = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            doi = (d.get("doi") or "").lower().strip()
            if not doi or not d.get("title"):
                continue
            if doi in recs:
                cur = recs[doi]
                cur["srcs"].add(d.get("src", "?"))
                cur["queries"].add(d.get("query", ""))
                cur["cats_src"].add(d.get("cat", ""))
                if not cur.get("abstract") and d.get("abstract"):
                    cur["abstract"] = d["abstract"]
                if not cur.get("authors") and d.get("authors"):
                    cur["authors"] = d["authors"]
                if not cur.get("journal") and d.get("journal"):
                    cur["journal"] = d["journal"]
                if not cur.get("issn") and d.get("issn"):
                    cur["issn"] = d["issn"]
                cur["cited_by"] = max(cur.get("cited_by") or 0, d.get("cited_by") or 0)
                cur["retracted"] = cur.get("retracted") or bool(d.get("retracted"))
            else:
                d["srcs"] = {d.get("src", "?")}
                d["queries"] = {d.get("query", "")}
                d["cats_src"] = {d.get("cat", "")}
                recs[doi] = d
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--raw", default="raw.jsonl")
    ap.add_argument("--out", default="selected.json")
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)
    cats = cfg["categories"]
    y0, y1 = int(cfg["year_from"]), int(cfg["year_to"])
    cur_year = y1
    rel_min = float(cfg.get("rel_min", 8))
    if_th = float(cfg.get("if_threshold", 5.0))
    hi_n = int(cfg.get("per_cat_high", 18))
    lo_n = int(cfg.get("per_cat_low", 8))
    cn_pick = int(cfg.get("cn_pick", 12))
    cn_issns = set(cfg.get("cn_issns") or [])

    recs = load_raw(args.raw)
    print("loaded unique DOI:", len(recs), flush=True)

    kept = []
    for r in recs.values():
        y = r.get("year") or 0
        if not (y0 <= y <= y1) or r.get("retracted"):
            continue
        r["title"] = clean(r.get("title"))
        r["journal"] = clean(r.get("journal"))
        ifv, matched = get_if(r["journal"])
        r["if"] = ifv
        r["if_matched"] = matched
        r["cite_vel"] = round((r.get("cited_by") or 0) / max(1, cur_year - y + 1), 2)
        for c in cats:
            s, hits = kw_score(r, c)
            r[f"rel_{c['name']}"] = s
            r[f"hits_{c['name']}"] = hits
        r["rel_best"] = max(r[f"rel_{c['name']}"] for c in cats)
        r["cat"] = max(cats, key=lambda c: r[f"rel_{c['name']}"])["name"]
        r["cats"] = [c["name"] for c in cats if r[f"rel_{c['name']}"] >= rel_min]
        if not r["cats"]:
            r["cats"] = [r["cat"]]
        kept.append(r)
    print("after year/relevance prep:", len(kept), flush=True)

    def score(r, cname):
        return (r["if"] * 1.0
                + min(r["cite_vel"], 60) * 0.7
                + r[f"rel_{cname}"] * 1.2
                + (4 if (r.get("year") or 0) >= y1 - 2 else 0)
                + (3 if r.get("if_matched") else 0))

    selected, seen = [], {}

    def add(r, tier):
        if r["doi"] in seen:
            return
        for k in ("srcs", "queries", "cats_src"):
            if isinstance(r.get(k), set):
                r[k] = sorted(r[k])
        r["tier"] = tier
        seen[r["doi"]] = r
        selected.append(r)

    for c in cats:
        cname = c["name"]
        # 必须命中至少一个 strong 词，避免仅靠 composite/friction 等宽泛词误收
        cand = [r for r in kept if r[f"rel_{cname}"] >= rel_min and r.get(f"hits_{cname}")]
        for r in cand:
            r[f"score_{cname}"] = round(score(r, cname), 2)
        cand.sort(key=lambda r: r[f"score_{cname}"], reverse=True)

        hi = [r for r in cand if r["if"] >= if_th]
        lo = [r for r in cand if 0 < r["if"] < if_th]
        n_hi = 0
        per_j = defaultdict(int)
        for r in hi:
            if per_j[r["journal"]] >= 3 or n_hi >= hi_n:
                continue
            per_j[r["journal"]] += 1
            add(r, "A")
            n_hi += 1
        n_lo = 0
        per_j2 = defaultdict(int)
        for r in lo:
            if per_j2[r["journal"]] >= 2 or n_lo >= lo_n:
                continue
            per_j2[r["journal"]] += 1
            add(r, "B")
            n_lo += 1
        print(f"{cname}: cand={len(cand)} A={n_hi} B={n_lo}", flush=True)

    # 国内主办期刊定向补充
    if cn_issns:
        cand = [r for r in kept
                if (r.get("issn") or "") in cn_issns and r["doi"] not in seen
                and r["rel_best"] >= rel_min
                and any(r.get(f"hits_{c['name']}") for c in cats)]
        for r in cand:
            r["score_cn"] = round(r["if"] + min(r["cite_vel"], 40) * 0.8
                                  + r["rel_best"] * 0.8
                                  + (4 if (r.get("year") or 0) >= y1 - 2 else 0), 2)
        cand.sort(key=lambda r: r["score_cn"], reverse=True)
        per_j = defaultdict(int)
        n = 0
        for r in cand:
            if per_j[r["journal"]] >= 4 or n >= cn_pick:
                continue
            per_j[r["journal"]] += 1
            add(r, "C")
            n += 1
        print(f"C (国内主办): {n}", flush=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=1)
    print("selected:", len(selected), "->", args.out, flush=True)


if __name__ == "__main__":
    main()
