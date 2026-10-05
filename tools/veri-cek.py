#!/usr/bin/env python3
"""
Fandom MediaWiki API'sinden ham wikitext çeker.
Kaynak: https://mushokaihanshokai.fandom.com  →  mushokutensei.fandom.com
Çıktı: tools/ham/raw/pages.json  (build_data.py bunu okur)
"""
import json, os, time, urllib.request, urllib.parse

API = "https://mushokutensei.fandom.com/api.php"
KOK = os.path.dirname(os.path.abspath(__file__))
HAM = os.path.join(KOK, "ham", "raw")
UA = "Mozilla/5.0 (Android; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0"


def api(p, tries=5):
    p = dict(p); p["format"] = "json"
    veri = urllib.parse.urlencode(p).encode()
    for i in range(tries):
        try:
            r = json.load(urllib.request.urlopen(
                urllib.request.Request(API, data=veri, headers={
                    "User-Agent": UA,
                    "Content-Type": "application/x-www-form-urlencoded"}), timeout=45))
            if "error" in r:
                print("   API hatası:", r["error"].get("code")); time.sleep(2 + i); continue
            return r
        except Exception as e:
            print("   tekrar", i, repr(e)[:60]); time.sleep(2 + i)
    return {}


def main():
    os.makedirs(HAM, exist_ok=True)

    # 1) sayfa listesi
    sayfalar, cont = [], None
    for _ in range(15):
        p = {"action": "query", "list": "allpages", "aplimit": "500"}
        if cont:
            p["apcontinue"] = cont
        d = api(p)
        sayfalar += [x["title"] for x in d.get("query", {}).get("allpages", [])]
        if "continue" in d:
            cont = d["continue"]["apcontinue"]
        else:
            break
        time.sleep(0.3)
    sayfalar = sorted(set(sayfalar))
    print(f"Sayfa listesi: {len(sayfalar)}")

    # 2) ham wikitext (POST, 50'şerlik)
    yol = os.path.join(HAM, "pages.json")
    veri = json.load(open(yol, encoding="utf-8")) if os.path.exists(yol) else {}
    eksik = [t for t in sayfalar if t not in veri]
    print("Eksik:", len(eksik))

    for i in range(0, len(eksik), 50):
        ch = eksik[i:i + 50]
        r = api({"action": "query", "prop": "revisions", "rvprop": "content",
                 "rvslots": "main", "redirects": "1", "titles": "|".join(ch)})
        q = r.get("query") or {}
        got = {}
        for _, sayfa in (q.get("pages") or {}).items():
            rev = sayfa.get("revisions") or []
            if rev and "*" in rev[0].get("slots", {}).get("main", {}):
                got[sayfa["title"]] = rev[0]["slots"]["main"]["*"]
        for m in list(q.get("normalized") or []) + list(q.get("redirects") or []):
            if m["to"] in got:
                got.setdefault(m["from"], got[m["to"]])
        veri.update(got)
        if i % 250 == 0:
            print(f"  {i}/{len(eksik)} toplam={len(veri)}")
        time.sleep(0.3)

    json.dump(veri, open(yol, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"Ham veri yazıldı: {len(veri)} sayfa → {yol}")


if __name__ == "__main__":
    main()
