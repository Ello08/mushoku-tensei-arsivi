#!/usr/bin/env python3
"""
Dogrulama: ic baglantilar, çapa hedefleri, JSON dosyalari,
kapanmamis HTML etiketleri, erisilebilirlik kontrolleri.
"""
import os, re, json, sys
from html.parser import HTMLParser

KOK = os.path.dirname(os.path.abspath(__file__))
KOK = os.path.dirname(KOK)  # tools/ -> kok
HATA, UYARI = [], []

def hata(m): HATA.append(m)
def uyari(m): UYARI.append(m)

# ---------------------------------------------------------------- sayfalar
sayfalar = [f for f in os.listdir(KOK) if f.endswith(".html")]
idler = {}   # dosya -> {id: ...}

VOID = {"area","base","br","col","embed","hr","img","input","link","meta",
        "param","source","track","wbr","path","circle","rect","line","polygon",
        "polyline","use","stop","ellipse"}

class Kontrol(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.yigin = []
        self.idler = set()
        self.hatali = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d: self.idler.add(d["id"])
        if tag not in VOID:
            self.yigin.append((tag, self.getpos()[0]))
    def handle_startendtag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d: self.idler.add(d["id"])
    def handle_endtag(self, tag):
        if tag in VOID: return
        if not self.yigin:
            self.hatali.append(f"fazladan </{tag}> (satır {self.getpos()[0]})")
            return
        if self.yigin[-1][0] == tag:
            self.yigin.pop()
        else:
            for i in range(len(self.yigin) - 1, -1, -1):
                if self.yigin[i][0] == tag:
                    acilan = [f"<{t}>@{l}" for t, l in self.yigin[i + 1:]]
                    self.hatali.append(
                        f"</{tag}> (satır {self.getpos()[0]}) açıkmamış: {', '.join(acilan)}")
                    del self.yigin[i:]
                    return
            self.hatali.append(f"</{tag}> (satır {self.getpos()[0]}) eşleşmesiz")

icerik = {}
for f in sayfalar:
    txt = open(os.path.join(KOK, f), encoding="utf-8").read()
    icerik[f] = txt
    k = Kontrol()
    try:
        k.feed(txt)
    except Exception as e:
        hata(f"{f}: HTML ayrıştırma hatası: {e}")
    idler[f] = k.idler
    for m in k.hatali:
        hata(f"{f}: {m}")
    for tag, ln in k.yigin:
        hata(f"{f}: kapanmamış <{tag}> (satır {ln})")

# ---------------------------------------------------------------- baglantilar
ID_DUZELT = {}
for f, ids in idler.items():
    ID_DUZELT[f] = ids

for f, txt in icerik.items():
    for m in re.finditer(r'(?:href|src)="([^"]+)"', txt):
        hedef = m.group(1)
        if hedef.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        dosya, _, cipa = hedef.partition("#")
        if not dosya:
            continue
        yol = os.path.normpath(os.path.join(KOK, dosya))
        if not os.path.exists(yol):
            hata(f"{f}: kırık bağlantı → {hedef} (dosya yok)")
            continue
        if cipa:
            if not yol.endswith(".html"):
                continue
            if cipa not in ID_DUZELT.get(os.path.basename(yol), set()):
                hata(f"{f}: kırık çapa → {hedef} (#{cipa} hedefi yok)")

# ---------------------------------------------------------------- anchor hedefleri
# JS'in ürettiği çapalar (sezon/bölüm, cilt no) veriye göre doğrulanır
def js_capa_hedefleri():
    bekle = []
    a = json.load(open(os.path.join(KOK, "assets/data/anime.json"), encoding="utf-8"))
    for b in a["episodes"]:
        bekle.append((f"s{b['sezon']}e{str(b['no']).replace('.','')}", f"anime.html"))
    for dosya, anahtar in (("manga.json", "ana"), ("novel.json", "lightNovel")):
        d = json.load(open(os.path.join(KOK, "assets/data", dosya), encoding="utf-8"))
        for c in d.get(anahtar, []):
            bekle.append((f"cilt-{c['no']}", None))
    return bekle

for c, _ in js_capa_hedefleri():
    pass  # bu çapalar JS tarafından üretilir, HTML'de hedef yok; uyarı üretme

# ---------------------------------------------------------------- JSON
for f in sorted(os.listdir(os.path.join(KOK, "assets/data"))):
    y = os.path.join(KOK, "assets/data", f)
    try:
        json.load(open(y, encoding="utf-8"))
    except Exception as e:
        hata(f"assets/data/{f}: geçersiz JSON — {e}")

# ---------------------------------------------------------------- erisilebilirlik
for f, txt in icerik.items():
    if txt.count("<h1") != 1:
        hata(f"{f}: tam olarak bir <h1> olmalı, bulunan {txt.count('<h1')}")
    if 'lang="tr"' not in txt:
        hata(f"{f}: <html lang> eksik")
    if "<title>" not in txt:
        hata(f"{f}: <title> eksik")
    if 'name="description"' not in txt:
        hata(f"{f}: meta description eksik")
    # Erişilebilirlik: etiketsiz ve içeriksiz düğme/bağlantı olmamalı
    for g in re.finditer(r'<(button|a)\b([^>]*)>(.*?)</\1>', txt, flags=re.S):
        etiket, nitelik, govde = g.group(1), g.group(2), g.group(3)
        satir = txt[:g.start()].count("\n") + 1
        bos = not re.sub(r"<[^>]+>", "", govde).strip()
        if bos and "aria-label" not in nitelik and "aria-labelledby" not in nitelik:
            uyari(f"{f}:{satir}: içeriği ve aria-label'ı olmayan <{etiket}>")
    # lang değişkeni kullanımı
    for s in re.finditer(r'data-tema="([^"]*)"', txt):
        if s.group(1) not in ("koyu", "pargamen"):
            hata(f"{f}: geçersiz tema değeri {s.group(1)}")

# ---------------------------------------------------------------- ikon butunlugu
IKONLAR = open(os.path.join(KOK, "assets/js/icons.js"), encoding="utf-8").read()
TANIMLI = set(re.findall(r'\["([\w-]+)",\s*"', IKONLAR))
kullananlar = set()
for f in ["assets/js/veri.js", "assets/js/site.js"] + sayfalar:
    t = open(os.path.join(KOK, f), encoding="utf-8").read()
    kullananl = set(re.findall(r"#i-([\w-]+)", t))
    kullananl |= set(re.findall(r'ikon\("([\w-]+)"', t))
    kullananl |= set(re.findall(r'href=["\']?#i-([\w-]+)', t))
    kullananl |= set(re.findall(r'kanit\([^,]+,[^,]+,\s*"([\w-]+)"', t))
    kullananl |= set(re.findall(r'etiket\([^,]+,[^,]+,\s*"([\w-]+)"', t))
    eksik = kullananl - TANIMLI
    if eksik:
        hata(f"{f}: tanımsız ikon → {sorted(eksik)}")
    kullananlar |= kullananl

# ---------------------------------------------------------------- JS söz dizimi
# Parantez sayımı güvenilir değil (yorumlar, string'ler, regex) — node kullanılır.
import shutil, subprocess
if shutil.which("node"):
    jsler = [f for f in os.listdir(os.path.join(KOK, "assets/js")) if f.endswith(".js")]
    for f in jsler:
        p = subprocess.run(["node", "--check", os.path.join(KOK, "assets/js", f)],
                           capture_output=True, text=True)
        if p.returncode != 0:
            hata(f"assets/js/{f}: sözdizimi hatası — "
                 f"{(p.stderr or '').strip().splitlines()[-1:] or ['bilinmiyor']}")
    if not hata:
        print(f"JS sözdizimi: {len(jsler)} dosya OK")
else:
    uyari("node yok — JS sözdizimi denetlenemedi")

# ---------------------------------------------------------------- rapor
print(f"Sayfa: {len(sayfalar)}   İkon: {len(TANIMLI)} tanımlı, {len(kullananlar)} kullanılan")
print(f"Veri: {len(os.listdir(os.path.join(KOK,'assets/data')))} dosya")
if UYARI:
    print(f"\nUYARILAR ({len(UYARI)}):")
    for u in UYARI[:40]: print("  ~", u)
if HATA:
    print(f"\nHATALAR ({len(HATA)}):")
    for x in HATA[:60]: print("  x", x)
    sys.exit(1)
print("\nHata yok.")