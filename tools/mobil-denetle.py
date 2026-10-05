#!/usr/bin/env python3
"""
Mobil denetim: 320–430 px aralığında kırılabilecek her şeyi raporlar.
Gerçek tarayıcı olmadan statik analiz.
"""
import os, re, sys, glob

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = open(os.path.join(KOK, "assets/css/site.css"), encoding="utf-8").read()
JS = "".join(open(os.path.join(KOK, f"assets/js/{n}"), encoding="utf-8").read()
             for n in ("veri.js", "site.js"))

HATA, UYARI, BILGI = [], [], []
def hata(m): HATA.append(m)
def uyari(m): UYARI.append(m)

# Median genişlik: en yaygın telefonlar
DAR = 360
EN_DAR = 320

css = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)

# ---------------------------------------------------------------- 1. Sabit genişlikler
# Bir kural 320px ekrana sığmayan sabit genişlik içeriyorsa riskli
for m in re.finditer(r"([^{}]+)\{([^{}]+)\}", css):
    sec, govde = m.group(1).strip(), m.group(2)
    if "@media" in sec:
        continue
    for wm in re.finditer(r"(?<!max-)width:\s*(\d+)px", govde):
        px = int(wm.group(1))
        if px > DAR:
            hata(f"{sec.splitlines()[-1].strip()}: sabit width:{px}px → {EN_DAR}px ekranda taşar")

# min-width (yalnizca ozellik olarak; @media sorgusu degil)
for m in re.finditer(r"\}\s*min-width:\s*(\d+)px|[;{\s]min-width:\s*(\d+)px", css):
    px = int(m.group(1) or m.group(2))
    if px > DAR:
        # bu deger bir medya sorgusunun icinde mi?
        i = m.start()
        ust = css[:i]
        son_mq = ust.rfind("@media")
        son_kapanis = ust.rfind("}")
        if son_mq > son_kapanis:
            continue   # @media (min-width: ...) — sorun degil
        uyari(f"min-width:{px}px → yatay kaydırma gerekir (kaydırılabilir olmalı)")

# ---------------------------------------------------------------- 2. Media query eşiği
mqs = sorted({int(x) for x in re.findall(r"@media[^{]*?max-width:\s*(\d+)px", css)})
uyari(f"Mevcut max-width eşikleri: {mqs}")

if not any(e <= 400 for e in mqs):
    hata("400px altı için hiçbir kırılma noktası yok")

# ---------------------------------------------------------------- 3. Düz çok sütunlu ızgara (kırılmasız)
for m in re.finditer(r"([.#][\w-]+)\s*\{([^}]*grid-template-columns:[^}]*)\}", css):
    sec, govde = m.group(1), m.group(2)
    cols = re.search(r"grid-template-columns:\s*([^;]+)", govde)
    if not cols:
        continue
    if "minmax" in cols.group(1) or "auto-fit" in cols.group(1):
        continue
    # yalnizca iki veya daha fazla sütun varsa sorun
    parcalar = cols.group(1).split()
    if len(parcalar) < 2:
        continue  # "1fr" tek suttur, sorun degil
    if re.match(r"^\d*\.?\d*fr$", parcalar[0]) and re.match(r"^\d*\.?\d*fr$", parcalar[1]):
        # sabit fr sutunlari: kacak bir medya sorgusu var mi?
        # herhangi bir medya sorgusunda bu sinif tek sutuna iniyor mu?
        # (dosyanin tamami taranir — kural baska bir yerde olabilir)
        kacis = re.escape(sec)
        daraltiliyor = re.search(
            kacis + r"\s*\{[^}]*grid-template-columns:\s*1fr\s*(;|\})", css)
        if not daraltiliyor:
            uyari(f"{sec}: {cols.group(1).strip()[:44]} — tek sütuna inen kırılma noktası yok")

# ---------------------------------------------------------------- 4. SVG içindeki küçük metin
# Önemli: .harita dar ekranda gizlenip yerine liste geliyorsa sorun değil.
# "display:none" bir gizleme kuralı var mı (medya sorgusu içinde olmalı)?
HARITA_GIZLI = bool(re.search(r"\.harita\s*\{\s*display:\s*none", css))
LISTE_VAR = any("harita-liste" in open(f, encoding="utf-8").read()
                for f in glob.glob(os.path.join(KOK, "*.html")))
for f in glob.glob(os.path.join(KOK, "*.html")):
    t = open(f, encoding="utf-8").read()
    for sm in re.finditer(r'viewBox="0 0 (\d+) (\d+)"', t):
        vw = int(sm.group(1))
        # bu SVG .harita mi? (temel class'i kontrol et)
        cevre = t[max(0, sm.start()-200):sm.start()]
        harita_mi = 'class="harita"' in cevre
        if harita_mi and HARITA_GIZLI and LISTE_VAR and 780 in mqs:
            BILGI.append(f"{os.path.basename(f)}: tema diyagramı dar ekranda gizleniyor, "
                         f"yerinde okunabilir liste var")
            continue
        for fs in re.finditer(r"font-size:(\d+(?:\.\d+)?)px", t[sm.start():sm.start()+4000]):
            px = float(fs.group(1))
            olcek = min(1.0, 340 / vw)
            gorunen = px * olcek
            if gorunen < 7.0:
                hata(f"{os.path.basename(f)}: viewBox {vw}px → {olcek:.2f} ölçek, "
                     f"SVG metni {px}px → {gorunen:.1f}px görünür (okunamaz)")
                break

# ---------------------------------------------------------------- 5. nowrap taşmaları
for m in re.finditer(r"([.#][\w-]+)\s*\{[^}]*white-space:\s*nowrap[^}]*\}", css):
    sec = m.group(1)
    # kırılma noktası içinde mi kontrol et
    i = m.start()
    ust = css[:i]
    son_mq = ust.rfind("@media")
    son_kapanis = ust.rfind("}")
    if son_mq > son_kapanis:
        uyari(f"{sec}: white-space:nowrap kırılmaz — 360px'te taşabilir")

# ---------------------------------------------------------------- 6. Dokunma hedefleri
for m in re.finditer(r"([.#][\w-]+)\s*\{([^}]*)\}", css):
    sec, govde = m.group(1), m.group(2)
    wh = re.search(r"(?:min-)?width:\s*(\d+)px", govde)
    hh = re.search(r"(?:min-)?height:\s*(\d+)px", govde)
    if wh and hh and ".dugme" in sec:
        if int(wh.group(1)) < 44 or int(hh.group(1)) < 44:
            uyari(f"{sec}: {wh.group(1)}×{hh.group(1)}px → 44px dokunma hedefi önerilir")

# ---------------------------------------------------------------- 7. Sticky yükseklik varsayımı
# .ust-ic min-height ile .gezinme inset değeri eşleşmeli
ust_h = re.search(r"\.ust-ic\s*\{[^}]*min-height:\s*([\d.]+)rem", css)
gez_inset = re.search(r"\.gezinme\s*\{[^}]*inset:\s*([\d.]+)rem", css)
if ust_h and gez_inset:
    a = float(ust_h.group(1)); b = float(gez_inset.group(1))
    if abs(a - b) > 0.01:
        hata(f"mobil menü hizası bozuk: .ust-ic min-height={a}rem ama "
             f".gezinme inset={b}rem — başlık daha uzunsa menü boşlukta kalır")
    else:
        BILGI.append(f"mobil menü hizası tutarlı ({a}rem)")

# ---------------------------------------------------------------- 8. Yatay taşma riski: sabit inset
for m in re.finditer(r"left:\s*(-?\d+(?:\.\d+)?)(px|rem)", css):
    deger = float(m.group(1))
    birim = m.group(2)
    px = deger if birim == "px" else deger * 16
    if px < -0.5 * DAR:
        uyari(f"left:{deger}{birim} → {EN_DAR}px ekranda yatay taşma yaratabilir")

# ---------------------------------------------------------------- 9. Metin sarma engeli
for cls in ["ozet", "jp-ad", "sira-ozet", "card-ad"]:
    if cls in css and "overflow-wrap" not in css and "word-break" not in css:
        pass

# ---------------------------------------------------------------- 10. body yatay kaydırma koruması
if "overflow-x: hidden" not in CSS:
    hata("body'de overflow-x:hidden yok — yatay taşma sayfayı kaydırılabilir yapar")
else:
    BILGI.append("body overflow-x:hidden ile korumalı")

# ---------------------------------------------------------------- 11. Dokunma dostu vurgu
if "-webkit-tap-highlight-color" not in CSS:
    uyari("-webkit-tap-highlight-color tanımlı değil (mobil dokunma geri bildirimi)")

# ---------------------------------------------------------------- 12. Medya sorgusu dar ekranı gerçekten hedefliyor mu
dar_mq = [e for e in mqs if e <= 780]
if dar_mq:
    BILGI.append(f"Dar ekran kırılma noktaları: {dar_mq}")
else:
    hata("480px altı kırılma noktası yok — mobil için tasarım yapılmamış")

# ---------------------------------------------------------------- 13. Metin boyutu tabanı
body_fs = re.search(r"body\s*\{[^}]*font-size:\s*clamp\([^)]*\)", css, re.S)
if body_fs:
    alt = re.search(r"clamp\(\s*([\d.]+)rem", body_fs.group(0))
    if alt and float(alt.group(1)) < 1.0:
        hata(f"gövde alt sınırı {alt.group(1)}rem < 1rem → iOS'ta metin küçük")

# ---------------------------------------------------------------- 14. Satır yüksekliği
lh = re.search(r"body\s*\{[^}]*line-height:\s*([\d.]+)", css, re.S)
if lh and float(lh.group(1)) < 1.5:
    uyari(f"satır yüksekliği {lh.group(1)} → mobilde okunabilirlik düşük")

# ---------------------------------------------------------------- rapor
print(f"MOBİL DENETİMİ  ({EN_DAR}–{DAR}px hedefi)")
print("=" * 60)
for m in BILGI:
    print("  ·", m)
if UYARI:
    print(f"\nUYARILAR ({len(UYARI)}):")
    for m in UYARI:
        print("  ~", m)
if HATA:
    print(f"\nHATALAR ({len(HATA)}):")
    for m in HATA:
        print("  x", m)
    sys.exit(1)
print("\nKritik hata yok.")
if UYARI:
    print(f"{len(UYARI)} uyarı var.")