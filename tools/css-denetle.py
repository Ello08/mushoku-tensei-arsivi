#!/usr/bin/env python3
"""
CSS denetimi:
  - HTML'de kullanılan ama CSS'te tanımsız sınıflar
  - CSS'te tanımlı ama hiç kullanılmayan sınıflar
  - Tanımsız CSS değişkenleri (var(--x) ama :root'ta --x yok)
  - Tema (koyu/parşömen) kapsama farkı
"""
import os, re, sys, glob

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = open(os.path.join(KOK, "assets/css/site.css"), encoding="utf-8").read()

HATA, UYARI, BILGI = [], [], []

# Bunlar sinif degil; CSS denetiminde gecilir
ETIKET_ADLARI = {
    "a", "article", "b", "br", "button", "code", "details", "div", "footer",
    "h1", "h2", "h3", "h4", "h5", "header", "img", "input", "kbd", "li",
    "main", "nav", "ol", "option", "p", "section", "select", "small", "span",
    "summary", "svg", "table", "tbody", "td", "th", "thead", "caption",
    "title", "tr", "ul", "blockquote", "dl", "dt", "dd", "aside", "caption",
    "path", "circle", "text", "use", "defs", "symbol", "rect", "line",
    "polygon", "polyline", "ellipse", "g", "figure", "time", "label",
}
YARDIMCI = {"null", "renk", "ad", "sinif", "s", "v", "x", "i", "n", "t",
            "b", "a", "e", "o", "u", "d", "c", "g", "k", "m", "p", "r"}

# CSS'teki tanımlı sınıflar
css_ust = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
tanimli = set(re.findall(r"\.([A-Za-zÇĞİÖŞÜçğıöşü_-][\wÇĞİÖŞÜçğıöşü-]*)", css_ust))

# HTML + JS'te kullanılan sınıflar
kullanilan = set()
dosyalar = glob.glob(os.path.join(KOK, "*.html")) + \
          glob.glob(os.path.join(KOK, "assets/js/*.js"))
for y in dosyalar:
    t = open(y, encoding="utf-8").read()
    for m in re.finditer(r'class="([^"]*)"', t):
        kullanilan.update(m.group(1).split())
    for m in re.finditer(r'className\s*=\s*"([^"]*)"', t):
        kullanilan.update(m.group(1).split())
    for m in re.finditer(r'classList\.(?:add|toggle|remove)\("([^"]+)"', t):
        kullanilan.add(m.group(1))
    # el("sinif", ...) / ikon("ad", "sinif") cagrilarindaki siniflari topla
    for m in re.finditer(r'\bel\(\s*"([\w-]+)"', t):
        kullanilan.add(m.group(1))
    for m in re.finditer(r'\bikon\(\s*"[\w-]+"\s*,\s*"([^"]+)"', t):
        kullanilan.update(m.group(1).split())
    # "+ x" ile birlestirilen sinif adlari
    for m in re.finditer(r'"\s*\+\s*(?:[a-z]+\s*\?\s*")?\s*([\w-]+)\s*\?', t):
        kullanilan.add(m.group(1))
    for m in re.finditer(r'etiket\(\s*[^,]+,\s*([a-z]+)\s*\?', t):
        kullanilan.add(m.group(1))
    for m in re.finditer(r'etiket\(\s*[^,]+,\s*\?\s*([\w-]+)\s*:', t):
        kullanilan.add(m.group(1))
    for m in re.finditer(r'kanit\(\s*[^,]+,\s*([\w-]+)\s*[,)]', t):
        kullanilan.add(m.group(1))
    for m in re.finditer(r'\.(?:kutu|levha|nota|basin|perde)\s*([\w-]*)\s*\+\s*', t):
        kullanilan.add(m.group(1))
    # gizli yardimci: HTML etiket adlari, JS parametre adlari, null
    kullanilan -= ETIKET_ADLARI | YARDIMCI
    # CSS içindeki dinamik sınıflar (template literal'ler)
    for m in re.finditer(r'"([a-zçğıöşü]+) "\+', t):
        kullanilan.add(m.group(1))

# --- 1) HTML'de var, CSS'te yok
eksik = sorted(k for k in kullanilan if k and k not in tanimli)
# SVG gibi ilgisiz şeyleri ele
eksik = [e for e in eksik if not e.startswith(("http", "svg", "mt-"))]
if eksik:
    UYARI.append(f"CSS'te tanımsız sınıf: {eksik}")
else:
    BILGI.append("Tüm kullanılan sınıflar CSS'te tanımlı")

# --- 2) CSS'te var, hiç kullanılmıyor
kullanilmayan = sorted(k for k in tanimli if k not in kullanilan)
if kullanilmayan:
    BILGI.append(f"Kullanılmayan CSS sınıfları ({len(kullanilmayan)}): "
                 + ", ".join(kullanilmayan[:25])
                 + ("…" if len(kullanilmayan) > 25 else ""))

# --- 3) CSS değişkenleri
kok_tanimli = set(re.findall(r"(--[\w-]+)\s*:", css_ust.split("html[data-tema")[0]))
parg_tanimli = set()
if "html[data-tema" in css_ust:
    parg_tanimli = set(re.findall(r"(--[\w-]+)\s*:",
                       css_ust.split("html[data-tema")[1].split("\n}")[0]))
VAR_DESEN = r"var\(\s*(--[\w-]+)"
kullanilan_var = set(re.findall(VAR_DESEN, css_ust))
# JS tarafında okunan değişkenler + JS'in OLUŞTURDUĞU sınıflar
js = "".join(open(os.path.join(KOK, f"assets/js/{n}"), encoding="utf-8").read()
             for n in ("site.js", "veri.js"))
kullanilan_var |= set(re.findall(VAR_DESEN, js))
# HTML'de inline kullanılanlar
for y in glob.glob(os.path.join(KOK, "*.html")):
    t = open(y, encoding="utf-8").read()
    kull = set(re.findall(VAR_DESEN, t))
    kull |= set(re.findall(r"(?:color|background|stroke|fill)\s*:\s*(--[\w-]+)", t))
    kullanilan_var |= kull
    eksik_html = sorted(k for k in kull if k not in kok_tanimli and k not in parg_tanimli)
    if eksik_html:
        HATA.append(f"{os.path.basename(y)}: tanımsız CSS değişkeni {eksik_html}")

# JS tarafindan calisma aninda atanan degiskenler (CSS'te olmamali)
CALISMA_ZAMANI = {"--gecikme"}
belirsiz = sorted(kullanilan_var - kok_tanimli - parg_tanimli - CALISMA_ZAMANI)
if belirsiz:
    HATA.append(f"Tanımsız CSS değişkeni: {belirsiz}")
else:
    BILGI.append(f"{len(kullanilan_var)} CSS değişkeni tanımlı ve kullanılıyor")

# --- 4) Tema kapsaması
for ad, kume in (("koyu", kok_tanimli), ("pargömen", parg_tanimli)):
    fark = sorted(kok_tanimli - kume)
    if fark and ad == "pargömen":
        BILGI.append("pargömen tema ana kök varsayılanlarını kullanıyor: " + ", ".join(fark[:12]))

# --- 5) Erişilebilirlik: prefers-reduced-motion
if "prefers-reduced-motion" not in CSS:
    UYARI.append("prefers-reduced-motion desteği yok")
else:
    BILGI.append("prefers-reduced-motion desteği var")

# --- 6) Yazdırma stilleri
if "@media print" not in CSS:
    UYARI.append("@media print bloğu yok")
else:
    BILGI.append("yazdırma stilleri var")

# --- 7) Dil dosyaları
if "Noto Serif JP" not in CSS:
    UYARI.append("Japonik yazı tipi (Noto Serif JP) tanımlı değil")
elif "Noto+Serif+JP" not in open(os.path.join(KOK, "index.html"), encoding="utf-8").read():
    UYARI.append("Noto Serif JP yüklenmiyor")
else:
    BILGI.append("Japonik yazı tipi yükleniyor")

# --- 8) focus-visible
BILGI.append("focus-visible stili var" if ":focus-visible" in CSS else "focus-visible stili YOK")

# --- 9) JS söz dizimi denetimi (node varsa)
import shutil as _sh, subprocess as _sp, tempfile as _tf
if _sh.which("node"):
    kotu = []
    for f in sorted(os.listdir(os.path.join(KOK, "assets/js"))):
        if not f.endswith(".js"):
            continue
        yol = os.path.join(KOK, "assets/js", f)
        p = _sp.run(["node", "--check", yol], capture_output=True, text=True)
        if p.returncode != 0:
            kotu.append(f"{f}: {p.stderr.strip().splitlines()[-1] if p.stderr else '?'}")
    if kotu:
        for k in kotu:
            HATA.append("JS sözdizimi · " + k)
    else:
        BILGI.append(f"{len([f for f in os.listdir(os.path.join(KOK, 'assets/js')) if f.endswith('.js')])} JS dosyası sözdizimi denetlendi")
else:
    UYARI.append("node yok — JS sözdizimi denetlenemedi (CI'da kuruludur)")

# ---------------------------------------------------------------- rapor
print("CSS DENETİMİ\n" + "=" * 56)
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
print("\nHata yok." + ("" if not UYARI else f" ({len(UYARI)} uyarı)"))