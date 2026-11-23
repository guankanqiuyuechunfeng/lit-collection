# -*- coding: utf-8 -*-
"""
多源文献检索：OpenAlex + Crossref（+ 国内主办期刊 ISSN 定向）

用法：
    python harvest.py --config config.json [--out raw.jsonl] [--only crossref|openalex|cn]

特性：
- 配置驱动：分类、检索式、年份范围全部来自 config.json
- 增量落盘：已完成的 job 记录在 <out>.done.json，中断后重跑自动跳过
- 限流稳健：指数退避重试；OpenAlex 429 不致命，Crossref 为主力源
- 统一字段：不同源的记录归一为同一 schema

输出 raw.jsonl，每行一条记录。
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

MAILTO_DEFAULT = "workbuddy@example.com"
UA = {"User-Agent": "LitCollection/2.0 (mailto:workbuddy@example.com)"}
OA_BASE = "https://api.openalex.org/works"
CR_BASE = "https://api.crossref.org/works"
CR_SELECT = ("DOI,title,container-title,issued,author,is-referenced-by-count,"
             "abstract,URL,ISSN,type")


def log(*a):
    print(*a, flush=True)


def http_json(url, tries=3, timeout=60):
    """带指数退避的 GET JSON；返回 (data, err)"""
    err = ""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r), ""
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            if "404" in str(e):
                return None, err
            wait = 4 * (2 ** i)
            time.sleep(wait)
    return None, err


def oa_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for w, idxs in inv.items():
        for i in idxs:
            pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))


def norm_rec(d):
    """统一字段、清洗 DOI"""
    d["doi"] = (d.get("doi") or "").lower().replace("https://doi.org/", "").strip()
    if not d.get("doi") or not d.get("title"):
        return None
    d.setdefault("year", None)
    d.setdefault("journal", "")
    d.setdefault("issn", "")
    d.setdefault("authors", [])
    d.setdefault("abstract", "")
    d.setdefault("cited_by", 0)
    d.setdefault("retracted", False)
    d.setdefault("oa_url", "")
    d["abstract"] = (d["abstract"] or "")[:2500]
    return d


def job_openalex(cat, q, sort, cfg):
    f = (f"from_publication_date:{cfg['year_from']}-01-01,"
         f"to_publication_date:{cfg['year_to']}-12-31,type:article")
    params = {"search": q, "filter": f, "sort": sort,
              "per-page": "50", "mailto": cfg.get("mailto", MAILTO_DEFAULT)}
    url = OA_BASE + "?" + urllib.parse.urlencode(params)
    data, err = http_json(url)
    if data is None:
        return [], err
    out = []
    for w in data.get("results", []):
        src = ((w.get("primary_location") or {}).get("source") or {})
        auths = [a.get("author", {}).get("display_name", "")
                 for a in (w.get("authorships") or [])[:15]]
        rec = norm_rec({
            "doi": w.get("doi") or "",
            "title": w.get("display_name") or "",
            "year": w.get("publication_year"),
            "date": w.get("publication_date"),
            "journal": src.get("display_name") or "",
            "issn": src.get("issn_l") or "",
            "cited_by": w.get("cited_by_count") or 0,
            "authors": [a for a in auths if a],
            "abstract": oa_abstract(w.get("abstract_inverted_index")),
            "oa_url": (w.get("open_access") or {}).get("oa_url") or "",
            "retracted": bool(w.get("is_retracted")),
            "cat": cat, "query": q, "src": "openalex", "_job": f"oa|{cat}|{q}|{sort}",
        })
        if rec:
            out.append(rec)
    return out, ""


def job_crossref(cat, q, sort, cfg, issn_filter=None):
    filt = (f"from-pub-date:{cfg['year_from']}-01-01,"
            f"until-pub-date:{cfg['year_to']}-12-31,type:journal-article")
    if issn_filter:
        filt = issn_filter + "," + filt
    params = {"query.bibliographic": q, "filter": filt,
              "rows": "40", "sort": sort, "order": "desc",
              "select": CR_SELECT, "mailto": cfg.get("mailto", MAILTO_DEFAULT)}
    url = CR_BASE + "?" + urllib.parse.urlencode(params)
    data, err = http_json(url)
    if data is None:
        return [], err
    out = []
    for it in data["message"]["items"]:
        auths = [((a.get("given") or "") + " " + (a.get("family") or "")).strip()
                 for a in (it.get("author") or [])[:15]]
        yr = (((it.get("issued", {}).get("date-parts") or [[None]])[0]) or [None])[0]
        rec = norm_rec({
            "doi": it.get("DOI") or "",
            "title": (it.get("title") or [""])[0],
            "year": yr,
            "journal": (it.get("container-title") or [""])[0],
            "issn": (it.get("ISSN") or [""])[0],
            "cited_by": it.get("is-referenced-by-count") or 0,
            "authors": [a for a in auths if a],
            "abstract": (it.get("abstract") or "")[:2500],
            "oa_url": it.get("URL") or "",
            "retracted": False,
            "cat": cat, "query": q,
            "src": "crossref-cn" if issn_filter else "crossref",
            "_job": f"cr{'cn' if issn_filter else ''}|{cat}|{q}|{sort}",
        })
        if rec:
            out.append(rec)
    return out, ""


def build_jobs(cfg, only):
    cats = cfg["categories"]
    jobs = []
    if only in (None, "all", "crossref"):
        for c in cats:
            for q in c["queries"]:
                for s in ("relevance", "is-referenced-by-count"):
                    jobs.append(("crossref", c["name"], q, s, None))
    if only in (None, "all", "cn") and cfg.get("cn_issns"):
        issn_filter = ",".join(f"issn:{i}" for i in cfg["cn_issns"])
        for c in cats:
            for q in c["queries"][:3]:
                for s in ("relevance", "is-referenced-by-count"):
                    jobs.append(("crossref", c["name"], q, s, issn_filter))
    if only in (None, "all", "openalex") and cfg.get("use_openalex", True):
        for c in cats:
            for q in c["queries"]:
                for s in ("relevance_score:desc", "cited_by_count:desc"):
                    jobs.append(("openalex", c["name"], q, s, None))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--out", default="raw.jsonl")
    ap.add_argument("--only", default="all",
                    choices=["all", "crossref", "openalex", "cn"])
    args = ap.parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = json.load(f)

    done_path = args.out + ".done.json"
    done = set(json.load(open(done_path, encoding="utf-8"))) if os.path.exists(done_path) else set()
    jobs = build_jobs(cfg, args.only)
    todo = [j for j in jobs if j[3] + "|" + j[0] + "|" + j[1] + "|" + j[2] +
            ("|cn" if j[4] else "") not in done]
    log(f"jobs total={len(jobs)} done={len(done)} todo={len(todo)}")

    ok = fail = 0
    with open(args.out, "a", encoding="utf-8") as fout:
        for i, j in enumerate(todo, 1):
            kind, cat, q, sort, issn = j
            key = sort + "|" + kind + "|" + cat + "|" + q + ("|cn" if issn else "")
            if kind == "openalex":
                recs, err = job_openalex(cat, q, sort, cfg)
            else:
                recs, err = job_crossref(cat, q, sort, cfg, issn)
            if err:
                fail += 1
                log(f"[{i}/{len(todo)}] FAIL {kind:8s} {cat} {q[:38]:38s} {err[:70]}")
            else:
                ok += 1
                for r in recs:
                    fout.write(json.dumps(r, ensure_ascii=False) + "\n")
                fout.flush()
                done.add(key)
                log(f"[{i}/{len(todo)}] {kind:8s} {cat} {q[:38]:38s} -> {len(recs)}")
            # 串行 + 间隔，避免 429；OpenAlex 失败也不影响整体
            time.sleep(0.45 if kind != "openalex" else 0.8)
            if i % 10 == 0:
                with open(done_path, "w", encoding="utf-8") as df:
                    json.dump(sorted(done), df, ensure_ascii=False)

    with open(done_path, "w", encoding="utf-8") as df:
        json.dump(sorted(done), df, ensure_ascii=False)
    log(f"finished ok={ok} fail={fail} -> {args.out}")


if __name__ == "__main__":
    main()
