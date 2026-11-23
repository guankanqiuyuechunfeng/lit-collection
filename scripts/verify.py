# -*- coding: utf-8 -*-
"""
逐条用 Crossref 核验 DOI，补全权威元数据（题名 / 期刊 / 年份 / 卷期页 / 作者）

用法：
    python verify.py --in selected.json --out verified.json

核验结果写入每条记录的 verify 字段：
  verified            完全一致
  mismatch:title/year 轻微差异（在线优先 vs 正式刊期、下标标记等，通常无害）
  not_found           Crossref 无此 DOI（保留原记录，不丢弃）
"""
import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "LitCollection/2.0 (mailto:workbuddy@example.com)"}


def norm(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def fetch_doi(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi) + "?mailto=workbuddy@example.com"
    for i in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)["message"]
        except Exception as e:
            if "404" in str(e):
                return None
            time.sleep(3 * (i + 1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="selected.json")
    ap.add_argument("--out", default="verified.json")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()

    with open(args.inp, encoding="utf-8") as f:
        items = json.load(f)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        metas = list(ex.map(fetch_doi, [it["doi"] for it in items]))

    out = []
    cnt = {"verified": 0, "mismatch": 0, "not_found": 0}
    for it, m in zip(items, metas):
        rec = dict(it)
        if not m:
            rec["verify"] = "not_found"
            cnt["not_found"] += 1
        else:
            t = (m.get("title") or [""])[0]
            j = (m.get("container-title") or [""])[0]
            yr = (((m.get("issued", {}).get("date-parts") or [[None]])[0]) or [None])[0]
            diff = []
            if norm(t)[:60] and norm(it["title"])[:60] and norm(t)[:60] != norm(it["title"])[:60]:
                diff.append("title")
            if yr and it.get("year") and int(yr) != int(it["year"]):
                diff.append("year")
            rec["cr_title"] = t
            rec["cr_journal"] = j
            rec["cr_year"] = yr
            rec["cr_volume"] = m.get("volume")
            rec["cr_issue"] = m.get("issue")
            rec["cr_page"] = m.get("page")
            rec["cr_authors"] = [((a.get("given") or "") + " " + (a.get("family") or "")).strip()
                                 for a in (m.get("author") or [])[:20]]
            if diff:
                rec["verify"] = "mismatch:" + ",".join(diff)
                cnt["mismatch"] += 1
            else:
                rec["verify"] = "verified"
                cnt["verified"] += 1
                rec["title_official"] = t
                rec["journal_official"] = j or it.get("journal")
                if yr:
                    rec["year"] = int(yr)
        out.append(rec)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"verified={cnt['verified']} mismatch={cnt['mismatch']} "
          f"not_found={cnt['not_found']} total={len(out)} -> {args.out}", flush=True)


if __name__ == "__main__":
    main()
