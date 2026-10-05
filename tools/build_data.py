#!/usr/bin/env python3
"""
Mushoku Tensei fandom verisini site için JSON veri katmanına çevirir.
Çıktı: assets/data/*.json  (prototip: içerik bu dosyalardan beslenir)
"""
import json, os, re, sys, html

HAM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ham")
RAW = os.path.join(HAM, "raw", "pages.json")
OUT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "..", "assets", "data"))

# ---------------------------------------------------------------- yardımcılar

def strip_templates(t, keep=None):
    """Şablonları içerik çıkarımıyla siler/değerlerini korur."""
    for _ in range(12):
        m = re.search(r"\{\{", t)
        if not m:
            break
        # eşleşen kapanışı bul
        depth, i = 0, m.start()
        while i < len(t):
            if t.startswith("{{", i):
                depth += 1; i += 2; continue
            if t.startswith("}}", i):
                depth -= 1; i += 2
                if depth == 0: break
                continue
            i += 1
        if i >= len(t):
            t = t[:m.start()]; break
        body = t[m.start() + 2:i - 2]
        t = t[:m.start()] + _template_value(body, keep) + t[i:]
    return t


def _template_value(body, keep):
    name = body.split("|", 1)[0].strip().lower()
    if keep and name in keep:
        # ilk değer satırını al
        for part in re.split(r"\n(?=[^|\n]|-)", body):
            if "=" in part:
                k, v = part.split("=", 1)
                if k.strip().lower() in keep:
                    return v.strip()
        return ""
    return " "


def clean(t, keep=None, links=True):
    if not t:
        return ""
    t = re.sub(r"<ref[^>]*?/>", "", t)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = strip_templates(t, keep)
    t = re.sub(r"\{\{[^{}]*\}\}", " ", t)
    if links:
        t = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", t)
        t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)
        t = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", t)
        t = re.sub(r"\[https?://\S+\]", "", t)
    t = re.sub(r"\{\{[^{}]*\}\}", " ", t)
    t = re.sub(r"</?(small|big|br|div|p|span|sup|sub|blockquote)[^>]*>", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"'''?", "", t)
    t = re.sub(r"''", "", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n\s*\n+", "\n\n", t)
    return t.strip()


def _balanced(text, start, op="{{", cl="}}"):
    """start konumundan başlayıp dengeli kapanışı bulur, (içerik, bitiş_idx) döner."""
    depth, i = 0, start
    while i < len(text):
        if text.startswith(op, i):
            depth += 1; i += len(op); continue
        if text.startswith(cl, i):
            depth -= 1; i += len(cl)
            if depth == 0:
                return text[start + len(op):i - len(cl)], i
            continue
        i += 1
    return None, len(text)


def _split_params(body):
    """Şablon gövdesini üst seviye '|' ile böler (iç içe şablon/link korunur)."""
    parts, buf, i = [], [], 0
    while i < len(body):
        if body.startswith("{{", i) or body.startswith("[[", i):
            op = "{{" if body.startswith("{{", i) else "[["
            cl = "}}" if op == "{{" else "]]"
            j = body.find(cl, i + 2)
            if j == -1:
                buf.append(body[i:]); break
            buf.append(body[i:j + len(cl)]); i = j + len(cl); continue
        if body[i] == "|":
            parts.append("".join(buf)); buf = []; i += 1; continue
        buf.append(body[i]); i += 1
    parts.append("".join(buf))
    return parts


def infobox(text, name_hint=None):
    """Sayfadaki ilk uygun infobox'tan {anahtar: değer} sözlüğü döndürür."""
    if not text:
        return {}
    for m in re.finditer(r"\{\{(Infobox[^\n|{]*)", text, flags=re.I):
        start = m.start()
        body, end = _balanced(text, start)
        if body is None:
            continue
        nm = m.group(1).strip().lower()
        if name_hint and name_hint.lower() not in nm:
            continue
        out = {}
        for part in _split_params(body)[1:]:
            part = part.strip()
            if not part:
                continue
            if "=" in part and re.match(r"^[^|<>\n]{1,40}\s*=", part):
                k, v = part.split("=", 1)
                k = k.strip().lower()
                out[k] = v.strip() if not out.get(k) else out[k].rstrip() + "\n" + v.strip()
            elif out:
                last = list(out)[-1]
                out[last] = out[last].rstrip() + "\n" + part
        if out:
            out["_infobox"] = nm
            return out
    return {}


def first_image(text):
    m = re.search(r"(?:^|\n)\s*(?:image|img|cover)\s*=\s*([^|\n}]+)", text, flags=re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"\[\[([^\]|]+\.(?:jpg|png|jpeg|gif))", text, flags=re.I)
    return m.group(1).strip() if m else None


def section(text, name):
    """'== Name ==' bölümünün metnini döndürür."""
    if not text:
        return ""
    m = re.search(r"^=+\s*" + re.escape(name) + r"\s*=+\s*$", text, flags=re.I | re.M)
    if not m:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^=+\s*[A-Za-z0-9].*?=+\s*$", rest, flags=re.M)
    return rest[:nxt.start()] if nxt else rest


def sentence_after(text, name, maxn=2):
    s = clean(section(text, name))
    parts = re.split(r"(?<=[.!?])\s+", s)
    return " ".join(parts[:maxn]).strip()


def romanize_JP(s):
    return s


def after_first_template(text):
    """İlk şablonu (varsa) atlayıp kalan metni döndürür."""
    m = re.search(r"\{\{", text)
    if not m:
        return text
    _, end = _balanced(text, m.start())
    return text[end:]


def trim(t, n):
    """Cümle sınırında keser; çok uzunsa elipsle kısaltır."""
    t = (t or "").strip()
    if len(t) <= n:
        return t
    cut = t[:n]
    sp = cut.rfind(". ")
    if sp > n * 0.55:
        return cut[:sp + 1]
    sp = cut.rfind(" ")
    return cut[:sp].rstrip(",;:") + "…"


# ---------------------------------------------------------------- yükle
P = json.load(open(RAW, encoding="utf-8"))
os.makedirs(OUT, exist_ok=True)


def w(name, data):
    path = os.path.join(OUT, name)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = max((len(v) for v in data.values() if isinstance(v, list)), default=len(data))
    print(f"  {name:22s} {n:5d} kayıt  ({os.path.getsize(path)//1024} KB)")


print("Veri katmanı üretiliyor...")

# ---------------------------------------------------------------- 1. ANIME
KEEP_EP = {"title", "image", "season", "episode", "airdate", "adaptation", "arc",
           "opening", "ending", "scriptwriter", "storyboard", "director",
           "animation_director", "series"}

episodes = []
MONTH = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
for title, body in P.items():
    ib = infobox(body)
    if not ib or "anime episode" not in ib.get("_infobox", ""):
        continue
    g = lambda k: clean(ib.get(k, ""), links=True)

    # --- bölüm adı: giriş paragrafındaki '''İngilizce''' (Kanji ''JP'') kalıbı
    lead = after_first_template(body)
    en = jp = ""
    m = re.search(r"'''\s*([^']{2,80}?)\s*'''", lead[:600])
    if m:
        en = m.group(1).strip()
        tail = lead[m.end():m.end() + 220]
        k = re.search(r"\(\s*([^()]{1,40}?)\s*''([^']{1,20}?)''\s*\)", tail)
        if k:
            jp = k.group(1).strip()
        else:
            k2 = re.search(r"''\s*([^']{1,20}?)\s*''", tail)
            if k2:
                jp = k2.group(1).strip()
    if not en:
        en = g("title") or title
    if not jp:
        jp = ""

    # --- tarihler: hem {{flags|ja|Japanese}} hem <sup>JP</sup> kalıpları
    air_raw = ib.get("airdate", "")
    air = re.sub(r"\{\{flags\|[^}]*\}\}", "\x00", air_raw)
    dates = re.findall(MONTH + r"\s+\d{1,2},\s+\d{4}", air)
    jp_date = en_date = ""
    for chunk in re.split(r"[\n*]", air):
        dd = re.findall(MONTH + r"\s+\d{1,2},\s+\d{4}", chunk)
        if not dd:
            continue
        if re.search(r"\x00\s*Japanese|Japanese|\bJP\b", chunk):
            jp_date = jp_date or dd[0]
        elif re.search(r"English|\bEN\b", chunk):
            en_date = en_date or dd[0]
    if not jp_date and dates:
        jp_date = dates[0]
    if not en_date and len(dates) > 1:
        en_date = dates[1]

    def as_int(v, default=0):
        n = re.sub(r"\D", "", v or "")
        return int(n) if n else default

    se = as_int(g("season"))
    ep_raw = clean(ib.get("episode", ""), links=False)
    ova = bool(re.search(r"OVA", ep_raw, re.I))
    ep_num = re.match(r"\s*(\d+)(?:\.(\d+))?", ep_raw)
    if not ep_num:
        continue
    ep = float(f"{ep_num.group(1)}.{ep_num.group(2)}") if ep_num.group(2) \
        else float(ep_num.group(1))
    if ep_num.group(2):
        ova = True                  # kesirli numaralar ek/OVA bölümler
    if se not in (1, 2, 3) or ep <= 0:
        continue

    syn = clean(section(body, "Synopsis") or section(body, "Summary"))
    episodes.append({
        "baslik": en,
        "wikiTitle": title,
        "jp": jp,
        "sezon": se,
        "bolum": ep,
        "bolumEt": int(ep) if float(ep).is_integer() else 0,
        "ova": ova,
        "airJp": jp_date,
        "airEn": en_date,
        "yay": g("arc").split("#")[-1].strip(),
        "acilis": "" if g("opening") in ("N/A", "-", "") else g("opening"),
        "kapanis": "" if g("ending") in ("N/A", "-", "") else g("ending"),
        "kaynak": g("adaptation").split("|")[-1].strip(),
        "senaryo": g("scriptwriter"),
        "yonetim": g("storyboard"),
        "rez": g("director"),
        "ozet": trim(" ".join(re.split(r"(?<=[.!?])\s+", syn)[:4]), 620),
        "kapak": first_image(body),
    })

# Aynı sezon+no için en uzun kaydı seç (redirect kopyalarını eler)
seen = {}
for e in sorted(episodes, key=lambda x: (x["sezon"], x["bolum"], len(x["ozet"]))):
    k = (e["sezon"], e["bolum"])
    if k not in seen or len(e["ozet"]) > len(seen[k]["ozet"]):
        seen[k] = e
episodes = sorted(seen.values(), key=lambda x: (x["sezon"], x["bolum"]))


def infobox_generic(page, keep=None):
    ib = infobox(P.get(page, ""), name_hint="infobox anime")
    return {k: clean(v) for k, v in ib.items() if not k.startswith("_") and k in (keep or set(ib))}


KEEP_S = {"title", "genre", "studio", "producer", "director", "writer", "storyboard",
          "status", "original run", "episodes", "networks", "licensors", "previous", "next",
          "image", "music", "title j", "title romanized", "title english", "yuusha", "plot"}


def season_meta(page, key):
    t = P.get(page, "")
    ib = infobox(t)
    raw = {k: clean(v) for k, v in ib.items() if not k.startswith("_")}
    tail = t.split("}}", 1)[-1] if "}}" in t[:600] else t[:1200]
    intro = clean(section(t, "Synopsis") or section(t, "Overview") or tail)
    return {
        "key": key,
        "baslik": clean(raw.get("title") or page),
        "jp": "",
        "studio": raw.get("studio", ""),
        "yapim": raw.get("producer", ""),
        "yonetmen": raw.get("director", ""),
        "senaryo": raw.get("writer", ""),
        "storyboard": raw.get("storyboard", ""),
        "durum": raw.get("status", ""),
        "donem": raw.get("original run", ""),
        "bolum": raw.get("episodes", ""),
        "kanallar": raw.get("networks", ""),
        "lisans": raw.get("licensors", ""),
        "muzik": raw.get("music", ""),
        "ozet": trim(" ".join(re.split(r"(?<=[.!?])\s+", intro)[:5]), 900),
        "bolumler": [e for e in episodes if e["sezon"] == key],
    }


seasons = [season_meta("Anime", 1), season_meta("Anime Season 2", 2), season_meta("Anime Season 3", 3)]
for e in episodes:
    e["bolum"] = int(e["bolum"]) if float(e["bolum"]).is_integer() else e["bolum"]
    e["no"] = str(e["bolum"])
    e["rez"] = re.sub(r"\s+", ", ", e["rez"])[:120]
    e["yay"] = re.sub(r"^(Mid-Level Adventurer|Entry-Level Adventurer)\s*Arc",
                      lambda m: m.group(1) + " Adventurer Arc", e["yay"])
w("anime.json", {"seasons": seasons, "episodes": episodes})

# ---------------------------------------------------------------- 2. MANGA
def volume_set(prefix, pattern, series_label, arcs=False):
    out = []
    for title, body in sorted(P.items()):
        m = re.fullmatch(pattern, title)
        if not m:
            continue
        ib = infobox(body)
        if not ib:
            continue
        num = m.group(1)
        rel = clean(ib.get("release", ""), keep={"release"})
        # tarihleri ayıkla
        dates = re.findall(r"([A-Z][a-z]+ \d{1,2}, \d{4})", rel)
        jp = next((x for x in dates if re.search(r"201[4-9]|202[0-6]", x)), dates[0] if dates else "")
        out.append({
            "no": num,
            "baslik": f"{series_label} {num}" + (" — " + (clean(ib.get("arc", "")).split("#")[-1].strip()) if arcs and ib.get("arc") else ""),
            "wikiTitle": title,
            "yazar": clean(ib.get("author", "")).replace("\n", " · "),
            "cizgi": clean(ib.get("cover", "")),
            "sayfa": clean(ib.get("pages", "")),
            "yayinJp": jp,
            "yayinTum": rel,
            "yayinci": clean(ib.get("publisher", "")).replace("\n", " · "),
            "isbn": clean(ib.get("isbn", "")),
            "onceki": clean(ib.get("previous", "")),
            "sonraki": clean(ib.get("next", "")),
            "ozet": trim(sentence_after(body, "Synopsis", 3) or sentence_after(body, "Summary", 3), 900),
            "kapak": first_image(body),
            "arc": clean(ib.get("arc", "")).split("#")[-1].strip(),
        })
    return out


manga_main = volume_set("Manga Volume", r"Manga Volume (\d+)", "Cilt", arcs=True)
manga_extra = []
for pat, lbl in [(r"4koma Vol (\d+)", "4-Koma"), (r"Eris Gaiden Manga Volume (\d+)", "Eris Gaiden"),
                 (r"Roxy Gets Serious Manga Volume (\d+)", "Roxy Gets Serious"),
                 (r"Depressed Magician Volume (\d+)", "Depressed Magician")]:
    manga_extra += volume_set("", pat, lbl)

for t in ["Anthology side: Roxy", "Anthology side: Eris", "Anthology side: Sylphy"]:
    body = P.get(t, "")
    if body:
        manga_extra.append({
            "no": "1", "baslik": t, "wikiTitle": t, "yazar": clean(infobox(body).get("author", "")),
            "cizgi": clean(infobox(body).get("cover", "")), "sayfa": clean(infobox(body).get("pages", "")),
            "yayinJp": "", "yayinTum": clean(infobox(body).get("release", "")),
            "yayinci": clean(infobox(body).get("publisher", "")), "isbn": "",
            "onceki": "", "sonraki": "",
            "ozet": trim(sentence_after(body, "Synopsis", 2), 700), "kapak": first_image(body), "arc": "",
        })

manga_page = P.get("Manga", "")
w("manga.json", {
    "ana": manga_main,
    "yan": manga_extra,
    "meta": {k: clean(v) for k, v in infobox(manga_page).items() if not k.startswith("_")},
    "ozet": trim(clean(section(manga_page, "Synopsis") or section(manga_page, "Overview")), 1200),
})

# ---------------------------------------------------------------- 3. NOVEL
ln = volume_set("Light Novel Volume", r"Light Novel Volume (\d+)", "Cilt", arcs=True)
wn = []
for title, body in sorted(P.items()):
    if not re.fullmatch(r"Web Novel Volume \d+", title):
        continue
    ib = infobox(body)
    if not ib:
        continue
    wn.append({"no": re.sub(r"\D", "", title), "baslik": title, "wikiTitle": title,
               "yayinJp": clean(ib.get("release", ""))[:120],
               "yayinci": clean(ib.get("publisher", "")),
               "yazar": clean(ib.get("author", "")),
               "ozet": trim(sentence_after(body, "Synopsis", 3) or sentence_after(body, "Summary", 3), 900)})

extras = []
for t in sorted(P):
    if re.match(r"(Light Novel Extra Edition Volume \d+|Redundant Reincarnation Volume \d+|Roxy Gets Serious Volume \d+)", t):
        body = P[t]
        ib = infobox(body)
        extras.append({
            "no": re.sub(r"\D", "", t), "baslik": t, "wikiTitle": t,
            "yazar": clean(ib.get("author", "")).replace("\n", " · "),
            "cizgi": clean(ib.get("illustrator", "")),
            "yayinJp": (re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", clean(ib.get("release", ""))) or [None, ""])[1]
            if re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", clean(ib.get("release", ""))) else "",
            "yayinTum": clean(ib.get("release", "")),
            "yayinci": clean(ib.get("publisher", "")),
            "sayfa": clean(ib.get("pages", "")),
            "ozet": trim(sentence_after(body, "Synopsis", 3) or sentence_after(body, "Summary", 3), 900),
            "kapak": first_image(body),
        })

novel_page = P.get("Light Novel", "")
wn_page = P.get("Web Novel", "")
w("novel.json", {
    "lightNovel": ln,
    "webNovel": wn,
    "ekstra": extras,
    "meta": {k: clean(v) for k, v in infobox(novel_page).items() if not k.startswith("_")},
    "metaWeb": {k: clean(v) for k, v in infobox(wn_page).items() if not k.startswith("_")},
    "ozet": trim(clean(section(novel_page, "Synopsis") or section(novel_page, "Overview")), 1200),
})

# ---------------------------------------------------------------- 4. KARAKTERLER
CHAR_KEEP = ["Rudeus Greyrat", "Roxy Migurdia", "Sylphiette", "Eris Boreas Greyrat",
             "Paul Greyrat", "Zenith Greyrat", "Lilia Greyrat", "Norn Greyrat", "Aisha Greyrat",
             "Ruijerd Superdia", "Orsted", "Hitogami", "Laplace", "Zanoba Shirone",
             "Ghislaine Dedoldia", "Elinalise Dragonroad", "Geese Nukadia", "Kishirika Kishirisu",
             "Auber Corvette", "Reida Lia", "Isolte Cruel", "Perugius Dola", "Gal Farion",
             "Nina Farion", "Gino Britts", "Cliff Grimoire", "Ariel Anemoi Asura",
             "Luke Notos Greyrat", "Nanahoshi Shizuka", "Shizuka Nanahoshi", "Juliette",
             "Jinas Halfas", "Linia Dedoldia", "Pursena Adoldia", "Gustav Dedoldia",
             "Gyes Dedoldia", "Minitona Dedoldia", "Rowin Migurdia", "Rokari Migurdia",
             "Badigadi", "Atoferatofe Rybak", "Moore", "Suzanne", "Sara", "Timothy",
             "Mimiru", "Patris", "Soldat Heckler", "Sieghart Saladin Greyrat",
             "Ars Greyrat", "Lara Greyrat", "Lucy Greyrat", "Lily Greyrat", "Christina Greyrat",
             "Sauros Boreas Greyrat", "Hilda Boreas Greyrat", "Philip Boreas Greyrat",
             "Soldat Heckler", "Almanfi", "Sylvaril", "Vita", "Dark King Vita",
             "Randolph Marianne", "Clive Grimoire", "Lunaria", "Eris Greyrat",
             "Roxy Migurdia Greyrat", "Sylphiette Greyrat", "Rude Mercenary Company"]

ROLE_MAP = {
    "Rudeus Greyrat": ("Ana", "gold"), "Roxy Migurdia": ("Ana", "mana"),
    "Sylphiette": ("Ana", "verdant"), "Eris Boreas Greyrat": ("Ana", "crimson"),
    "Paul Greyrat": ("Greyrat", "amber"), "Zenith Greyrat": ("Greyrat", "violet"),
    "Lilia Greyrat": ("Greyrat", "amber"), "Norn Greyrat": ("Greyrat", "violet"),
    "Aisha Greyrat": ("Greyrat", "verdant"), "Ruijerd Superdia": ("Yol arkadaşı", "crimson"),
    "Orsted": ("Antagonist", "violet"), "Hitogami": ("Antagonist", "violet"),
    "Laplace": ("Antagonist", "crimson"), "Zanoba Shirone": ("Ranoa", "gold"),
    "Ghislaine Dedoldia": ("Eski dostlar", "verdant"), "Elinalise Dragonroad": ("Eski dostlar", "verdant"),
    "Geese Nukadia": ("Eski dostlar", "gold"), "Kishirika Kishirisu": ("Demon", "violet"),
    "Auber Corvette": ("Yedi Güç", "mana"), "Reida Lia": ("Su İlahı", "mana"),
    "Isolte Cruel": ("Su İlahı", "mana"), "Perugius Dola": ("Kaos Kırıcı", "crimson"),
    "Gal Farion": ("Kılıç Kutsalı", "gold"), "Nina Farion": ("Kılıç Kutsalı", "crimson"),
    "Gino Britts": ("Kılıç Kutsalı", "gold"), "Cliff Grimoire": ("Ranoa", "gold"),
    "Ariel Anemoi Asura": ("Ranoa", "violet"), "Luke Notos Greyrat": ("Ranoa", "gold"),
    "Nanahoshi Shizuka": ("Ranoa", "mana"), "Juliette": ("Ranoa", "verdant"),
    "Jinas Halfas": ("Ranoa", "gold"), "Linia Dedoldia": ("Hayvan", "verdant"),
    "Pursena Adoldia": ("Hayvan", "verdant"), "Gustav Dedoldia": ("Hayvan", "amber"),
    "Gyes Dedoldia": ("Hayvan", "amber"), "Minitona Dedoldia": ("Hayvan", "verdant"),
    "Rowin Migurdia": ("Migurd", "mana"), "Rokari Migurdia": ("Migurd", "mana"),
    "Badigadi": ("Demon", "violet"), "Atoferatofe Rybak": ("Demon", "violet"),
    "Moore": ("Demon", "violet"), "Suzanne": ("Karşı Ok", "gold"),
    "Sara": ("Karşı Ok", "crimson"), "Timothy": ("Karşı Ok", "mana"),
    "Mimiru": ("Karşı Ok", "verdant"), "Patris": ("Karşı Ok", "gold"),
    "Soldat Heckler": ("Karşı Ok", "crimson"),
    "Sieghart Saladin Greyrat": ("Çocuklar", "verdant"), "Ars Greyrat": ("Çocuklar", "crimson"),
    "Lara Greyrat": ("Çocuklar", "mana"), "Lucy Greyrat": ("Çocuklar", "verdant"),
    "Lily Greyrat": ("Çocuklar", "mana"), "Christina Greyrat": ("Çocuklar", "crimson"),
    "Sauros Boreas Greyrat": ("Boreas", "amber"), "Hilda Boreas Greyrat": ("Boreas", "amber"),
    "Philip Boreas Greyrat": ("Boreas", "amber"), "Almanfi": ("Kaos Kırıcı", "mana"),
    "Sylvaril": ("Kaos Kırıcı", "verdant"), "Vita": ("Antagonist", "violet"),
    "Dark King Vita": ("Antagonist", "violet"), "Randolph Marianne": ("Ranoa", "crimson"),
    "Clive Grimoire": ("Ranoa", "gold"), "Lunaria": ("Ranoa", "mana"),
    "Eris Greyrat": ("Ana", "crimson"), "Roxy Migurdia Greyrat": ("Ana", "mana"),
    "Sylphiette Greyrat": ("Ana", "verdant"),
}

chars = []
for name in CHAR_KEEP:
    body = P.get(name)
    if not body:
        continue
    ib = infobox(body)
    grp, tone = ROLE_MAP.get(name, ("Diğer", "gold"))
    story = clean(section(body, "Story") or section(body, "Plot"))
    if len(story) < 200:
        story = clean(section(body, "Overview") or section(body, "History") or section(body, "Background"))
    pers = ""
    if ib:
        for k in ("personality", "appearance", "abilities", "powers and abilities"):
            v = clean(ib.get(k, ""))
            if len(v) > len(pers):
                pers = v
    chars.append({
        "ad": name,
        "jp": re.sub(r"^.*?\((.+?)\)", r"\1", body.replace("\n", " ")[:200], count=1) if "(" in body[:200] else "",
        "grup": grp,
        "ton": tone,
        "rol": clean(ib.get("role", "")) or clean(ib.get("occupation", "")),
        "baslangic": sentence_after(body, "Appearance", 1),
        "kisisellik": (re.split(r"(?<=[.!?])\s+", pers)[0] if pers else ""),
        "ozet": trim(" ".join(re.split(r"(?<=[.!?])\s+", story)[:5]), 700),
        "wiki": f"https://mushokutensei.fandom.com/wiki/{name.replace(' ', '_')}",
    })

w("karakterler.json", {
    "karakterler": chars,
    "gruplar": sorted({c["grup"] for c in chars}),
    "ozet": trim(clean(section(P.get("Characters", ""), "Overview") or section(P.get("Characters", ""), "Synopsis")), 800),
})

# ---------------------------------------------------------------- 5. YAYLAR / BÖLÜMLER
arcs_raw = P.get("Story Arcs", "") or P.get("List of Web Novel Arcs", "")
parts, cur_part, cur_arc, buf = [], None, None, []
for line in arcs_raw.split("\n"):
    h3 = re.match(r"^===\s*([^=].*?)\s*===$", line)
    h2 = re.match(r"^==\s*([^=].*?)\s*==$", line)
    if h2:
        if cur_arc:
            parts.append({"part": cur_part, "ad": cur_arc, "ozet": clean("\n".join(buf))})
        cur_part, cur_arc, buf = clean(h2.group(1)), None, []
    elif h3:
        if cur_arc:
            parts.append({"part": cur_part, "ad": cur_arc, "ozet": clean("\n".join(buf))})
        cur_arc, buf = clean(h3.group(1)), []
    elif cur_arc:
        buf.append(line)
if cur_arc:
    parts.append({"part": cur_part, "ad": cur_arc, "ozet": clean("\n".join(buf))})

for i, p in enumerate(parts):
    txt = p["ozet"]
    p["ozet"] = trim(" ".join(re.split(r"(?<=[.!?])\s+", txt)[:7]), 1100)
w("yaylar.json", {"yaylar": [p for p in parts if p["ozet"]]})

# ---------------------------------------------------------------- 6. DÜNYA & KAVRAMLAR
world_pages = ["Races", "Magic", "Mana", "Magic Spells", "Teleport Incident",
               "Seven Great Powers", "Seven Great World Powers", "Sword God Style",
               "Water God Style", "North God Style", "Sword Sanctuary", "Holy Land of Swords",
               "Demon Continent", "Central Continent", "Fittoa Region", "Millis Continent",
               "Millis Religion", "Human-Demon Wars", "Great Human-Demon Wars",
               "First Human-Demon War", "Second Human-Demon War", "Six-Faced World",
               "Ranoa University of Magic", "Adventure Guild", "Beast Race", "Elf",
               "Human", "Migurd", "Supard Tribe", "Dragon Tribe", "Heaven Race", "Dwarf",
               "Ogre race", "Dragon God", "Curses", "Barrier Magic", "Swordsmanship",
               "Milishion", "Chaos Breaker", "Floating Fortress", "Demon Lord", "Monsters",
               "Languages", "Terminology", "Names and Terminology", "World Map",
               "ORSTED Corporation", "Rude Mercenary Company", "Gods"]

world = []
for t in world_pages:
    body = P.get(t)
    if not body:
        continue
    ib = infobox(body)
    intro = clean(body.split("}}")[-1] if ib else body[:900])
    secs = []
    for m in re.finditer(r"^={2,3}\s*(.+?)\s*={2,3}$", body, flags=re.M):
        name = clean(m.group(1), links=False)
        txt = clean(section(body, name), links=True)
        if len(txt) > 180:
            secs.append({"ad": name, "metin": trim(" ".join(re.split(r"(?<=[.!?])\s+", txt)[:8]), 1400)})
    world.append({
        "ad": t,
        "tur": ib.get("type", "") or ib.get("race", "") or ib.get("style", "") or "",
        "ozet": trim(" ".join(re.split(r"(?<=[.!?])\s+", intro)[:6]), 900),
        "bolumler": secs[:6],
        "wiki": f"https://mushokutensei.fandom.com/wiki/{t.replace(' ', '_')}",
    })
w("dunya.json", {"konular": world})

# ---------------------------------------------------------------- 7. TEMALAR (lora)
concept_pages = ["Hitogami", "Fate", "Destiny", "Reality", "Gods", "Human God", "Man-God",
                 "Laplace", "Orsted", "Ruijerd Superdia", "Rudeus Greyrat",
                 "Teleport Incident", "Teleportation Labyrinth", "I Don't Want to Die",
                 "Existence", "Redundancy", "Seven Great Powers", "Gates of the Labyrinth"]
concepts = []
for t in concept_pages:
    body = P.get(t)
    if not body:
        continue
    txt = clean(body)
    txt = re.sub(r"^.*?(?=[A-Z][a-z]+\s+is\s+)", "", txt, count=1) if len(txt) > 900 else txt
    concepts.append({
        "ad": t,
        "jp": "",
        "ozet": trim(" ".join(re.split(r"(?<=[.!?])\s+", txt)[:9]), 1400),
        "wiki": f"https://mushokutensei.fandom.com/wiki/{t.replace(' ', '_')}",
    })
w("temalar.json", {"kavramlar": concepts})

# ---------------------------------------------------------------- 8. EK MEDYA
extra_media = []
for t, kind in [("Drama CD", "Audio drama"), ("Mobile Game", "Oyun"),
                ("Quest of Memories", "Oyun"), ("Recollection (light novel)", "Ek kitap"),
                ("Special Book", "Ek kitap"), ("Light Novel Special Book", "Ek kitap"),
                ("Blu-ray", "Medya"), ("Blu-ray Season 2", "Medya"), ("Blu-ray Season 3", "Medya"),
                ("Rifujin na Magonote", "Yaratıcı ekip"), ("Shirotaka", "Yaratıcı ekip")]:
    body = P.get(t)
    if not body:
        continue
    ib = infobox(body)
    extra_media.append({
        "ad": t, "tur": kind,
        "yayin": clean(ib.get("release", ""))[:200],
        "yayinci": clean(ib.get("publisher", "")) or clean(ib.get("studio", "")),
        "ozet": trim(" ".join(re.split(r"(?<=[.!?])\s+", clean(body.split("}}")[-1] if ib else body[:900]))[:6]), 800),
        "wiki": f"https://mushokutensei.fandom.com/wiki/{t.replace(' ', '_')}",
    })
w("ek-medya.json", {"kayitlar": extra_media})

print("\nBitti ->", os.path.normpath(OUT))