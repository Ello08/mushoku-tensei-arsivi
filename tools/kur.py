#!/usr/bin/env python3
"""
Statik site montajlayıcı.
src/sablon.html + src/sayfa/*.html  ->  site kökü (*.html)
Çıktı tamamen statiktir; veri katmanı (assets/data/*.json) tarayıcıda yüklenir.
"""
import os, re, json, shutil, sys

KOK = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(KOK, "src")
SAYFA = os.path.join(SRC, "sayfa")

MENU = [
    ("index.html", "Ana Sayfa", "hedef"),
    ("anime.html", "Anime", "film"),
    ("manga.html", "Manga", "kitap"),
    ("novel.html", "Novel", "kalem"),
    ("karakterler.html", "Karakterler", "kilic"),
    ("dunya.html", "Dünya", "harita"),
    ("yaylar.html", "Yaylar", "katlanir"),
    ("analiz.html", "Analiz", "buyut"),
    ("rehber.html", "Rehber", "hedef"),
    ("medya-eklenti.html", "Ek Medya", "disk"),
    ("hakkinda.html", "Hakkında", "belge"),
]

OMURGA_AD = {
    "index.html": ("無職転生", "Ansiklopedi"),
    "anime.html": ("試写", "Anime"),
    "manga.html": ("漫画", "Manga"),
    "novel.html": ("小説", "Novel"),
    "karakterler.html": ("人物", "Kişiler"),
    "dunya.html": ("世界", "Dünya"),
    "yaylar.html": ("物語", "Yaylar"),
    "analiz.html": ("考察", "Analiz"),
    "rehber.html": ("案内", "Rehber"),
    "medya-eklenti.html": (" liking", "Ek Medya"),
    "hakkinda.html": ("断章", "Hakkında"),
    "404.html": ("四〇四", "Bulunamadı"),
}
OMURGA_AD["medya-eklenti.html"] = ("付録", "Ek Medya")


def ikon(ad, sinif="ikon"):
    return f'<svg class="{sinif}" aria-hidden="true" focusable="false"><use href="#i-{ad}"></use></svg>'


def menu_html(aktif):
    out = []
    for yol, ad, _ in MENU:
        a = "aktif" if yol == aktif else ""
        out.append(f'<a class="gez {a}" href="{yol}">{ad}</a>')
    return "\n      ".join(out)


def alt_menu():
    gruplar = [
        ("Medya", [("anime.html", "Anime", "film"), ("manga.html", "Manga", "kitap"),
                   ("novel.html", "Novel", "kalem"), ("medya-eklenti.html", "Ek medya", "disk")]),
        ("Araştır", [("karakterler.html", "Karakterler", "kilic"), ("dunya.html", "Dünya & sistemler", "harita"),
                     ("yaylar.html", "Yaylar", "katlanir"), ("analiz.html", "Tematik analiz", "buyut")]),
        ("Rehber", [("rehber.html", "Nereden başlamalı", "hedef"), ("hakkinda.html", "Hakkında & kaynakça", "belge"),
                    ("404.html", "404", "kapat")]),
    ]
    out = []
    for baslik, ogeler in gruplar:
        li = "\n        ".join(
            f'<li><a href="{y}">{ikon(i, "ikon")} {a}</a></li>' for y, a, i in ogeler)
        out.append(f"<div><h4>{baslik}</h4><ul>\n        {li}\n      </ul></div>")
    return "\n      ".join(out)


def altin_svg(sinif="altin", donerli=True):
    """Altı Yüzlü Dünya motifi (vesica piscis) + büyü halkaları."""
    return f"""<svg class="{sinif}" viewBox="0 0 120 120" aria-hidden="true" focusable="false">
      <g class="{'doner' if donerli else ''}">
        <circle cx="46" cy="60" r="30" fill="none" stroke="currentColor" stroke-width="1.1"/>
        <circle cx="74" cy="60" r="30" fill="none" stroke="currentColor" stroke-width="1.1"/>
        <path d="M46 30a30 30 0 000 60 30 30 0 000-60z" fill="none" stroke="currentColor" stroke-width=".7" opacity=".55"/>
        <path d="M74 30a30 30 0 010 60 30 30 0 010-60z" fill="none" stroke="currentColor" stroke-width=".7" opacity=".55"/>
      </g>
      <g class="isik">
        <circle cx="60" cy="60" r="5.5" fill="currentColor" opacity=".8"/>
      </g>
      <circle cx="60" cy="60" r="46" fill="none" stroke="currentColor" stroke-width=".6"
              stroke-dasharray="2 6" opacity=".6"/>
    </svg>"""


def buyulu_cember(sinif="cember", uretecegimiz=False):
    """Rudeus'un büyü çemberi: iç içe daireler, yazı sıraları, altıgen."""
    kimlik = "c" if uretecegimiz else ""
    return f"""<svg class="{sinif}" viewBox="0 0 320 320" aria-hidden="true" focusable="false">
      <g class="yavas" fill="none" stroke="currentColor" stroke-linecap="round">
        <circle cx="160" cy="160" r="152" stroke-width="1" stroke-dasharray="1 7"/>
        <circle cx="160" cy="160" r="138" stroke-width=".6" opacity=".55"/>
        <circle cx="160" cy="160" r="104" stroke-width="1.4"/>
        <circle cx="160" cy="160" r="96" stroke-width=".5" stroke-dasharray="14 6" opacity=".7"/>
        <circle cx="160" cy="160" r="72" stroke-width=".9" opacity=".8"/>
        <path d="M160 8 L291 244 L29 244 Z" stroke-width=".7" opacity=".45"/>
        <path d="M160 312 L29 76 L291 76 Z" stroke-width=".7" opacity=".45"/>
      </g>
      <g class="ter" fill="none" stroke="currentColor" stroke-width=".7" opacity=".8">
        <path d="M160 24 L284 268 L36 268 Z"/>
        <circle cx="160" cy="160" r="58" stroke-dasharray="3 5"/>
        <circle cx="160" cy="160" r="30" stroke-width="1.1"/>
      </g>
      <g class="nabiz" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" opacity=".9">
        <path d="M148 160 h24 M160 148 v24"/>
      </g>
    </svg>"""


SABLON = """<!DOCTYPE html>
<html lang="tr" data-tema="pargamen">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{BASLIK} · Mushoku Tensei Ansiklopedisi</title>
<meta name="description" content="{ACIKLAMA}">
<meta name="author" content="Mushoku Tensei Ansiklopedisi (hayran projesi)">
<meta property="og:type" content="website">
<meta property="og:title" content="{BASLIK} · Mushoku Tensei Ansiklopedisi">
<meta property="og:description" content="{ACIKLAMA}">
<meta property="og:locale" content="tr_TR">
<meta name="theme-color" content="#070c16">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='13' cy='16' r='9' fill='none' stroke='%23d9a441' stroke-width='1.6'/%3E%3Ccircle cx='19' cy='16' r='9' fill='none' stroke='%2357bdd4' stroke-width='1.6'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Marcellus&family=Spectral:ital,wght@0,300;0,400;0,600;1,400&family=JetBrains+Mono:wght@400;700&family=Noto+Serif+JP:wght@400;700&display=swap">
<link rel="stylesheet" href="assets/css/site.css">
{EXTRA_KOPKA}
</head>
<body>

<div class="ilerleme" role="presentation"></div>

<div class="omurga" aria-hidden="true">
  <div class="omurga-marka">{OMURGA_JP}</div>
  <div class="omurga-cizgi"></div>
  <div class="omurga-yazi">{BOLUM_AD}</div>
  <div class="omurga-cizgi"></div>
  <div class="omurga-sayfa">{FOLYO}</div>
</div>

<header class="ust">
  <div class="defter ust-ic">
    <a class="marka" href="index.html" aria-label="Ana sayfa">
      {MUHUR}
      <span class="marka-yazi">
        <b>Mushoku Tensei</b>
        <span>Ansiklopedi · Fan Arşivi</span>
      </span>
    </a>

    <nav class="gezinme" aria-label="Ana gezinme">
      {MENU}
    </nav>

    <div class="ust-eylem">
      <button class="dugme" type="button" data-arama-ac aria-label="Ara (Ctrl+K)" title="Ara · Ctrl+K">
        <svg class="ikon" aria-hidden="true"><use href="#i-ara"></use></svg>
      </button>
      <button class="dugme" type="button" data-tema-dugme aria-label="Temayı değiştir" title="Temayı değiştir">
        <svg class="ikon" aria-hidden="true"><use href="#i-ay"></use></svg>
      </button>
      <button class="dugme menu-dugme" type="button" aria-expanded="false" aria-label="Menü" data-menu>
        <svg class="ikon" aria-hidden="true"><use href="#i-menu"></use></svg>
      </button>
    </div>
  </div>
</header>

<div class="arama-kat" id="arama-kat" role="dialog" aria-modal="true" aria-label="Arama">
  <div class="arama-kutu">
    <div class="arama-girdi">
      <svg class="ikon" aria-hidden="true"><use href="#i-ara"></use></svg>
      <input id="arama-girdi" type="search" placeholder="Karakter, bölüm, cilt, kavram ara…" autocomplete="off" spellcheck="false">
      <button class="dugme" type="button" data-arama-kapat aria-label="Kapat">
        <svg class="ikon" aria-hidden="true"><use href="#i-kapat"></use></svg>
      </button>
    </div>
    <div class="arama-sonuc" id="arama-sonuc"></div>
    <div class="arama-alt">
      <span><kbd>↑</kbd><kbd>↓</kbd> gez</span>
      <span><kbd>Enter</kbd> aç</span>
      <span><kbd>Esc</kbd> kapat</span>
      <span style="margin-left:auto">62 bölüm · 23 yay · 25 manga cilti · 26 novel cildi</span>
    </div>
  </div>
</div>

<main id="icerik">
{ICERIK}
</main>

<footer class="alt">
  <div class="defter">
    <div class="alt-izgara">
      <div>
        <h4>Bu arşiv ne</h4>
        <p style="font-size:.9rem;color:var(--soluk);max-width:44ch">
          <em>Mushoku Tensei: ~Isekai Ittara Honki Dasu~</em> üzerine Türkçe bir hayran ansiklopedisi.
          Bölüm, cilt ve kavram verileri Mushoku Tensei Wiki'den çekilmiş; tematik okumalar ve
          yorumlar bu sitenin kendi çalışmasıdır.
        </p>
        <p class="kanitler" style="margin-top:1rem">
          <span class="kanit">Yazar: Rifujin na Magonote</span>
          <span class="kanit mana">Çizim: Shirotaka</span>
        </p>
      </div>
      {ALT_MENU}
    </div>
    <div class="alt-son">
      <span>© {YIL} · hayran projesi. <strong>Resmî değildir</strong> — tüm haklar Rifujin na Magonote, Shirotaka,
      Media Factory, Studio Bind ve ilgili yapımlara aittir. Resim/kapak kullanılmaz; veriler alıntıdır.</span>
      <span class="mono">Veri: mushokutensei.fandom.com · Sürüm {SURUM}</span>
    </div>
  </div>
</footer>

<button class="yukari" type="button" aria-label="Yukarı çık">
  <svg class="ikon" aria-hidden="true"><use href="#i-yukari"></use></svg>
</button>

<script src="assets/js/icons.js"></script>
<script src="assets/js/site.js"></script>
<script src="assets/js/veri.js"></script>
{EXTRA_SCRIPT}
</body>
</html>
"""


def temizle(s):
    """Sayfa parçasındaki @satir@ işaretlerini HTML'e çevirir (mini şablon)."""
    def ikon_deg(m):
        ad, sinif = m.group(1), m.group(2) or ""
        c = "ikon" + ((" " + sinif) if sinif else "")
        return f'<svg class="{c}" aria-hidden="true" focusable="false"><use href="#i-{ad}"></use></svg>'

    s = re.sub(r"@ikon:([\w-]+)(?:\(([\w \-]*)\))?@", ikon_deg, s)
    s = re.sub(r"@altin:([\w \-]*)@", lambda m: altin_svg(m.group(1) or "altin"), s)
    s = re.sub(r"@cember:([\w \-]*)@", lambda m: buyulu_cember(m.group(1) or "cember"), s)
    return s


ETIKETLER = {"baslik", "aciklama", "folio", "ekstra-kopka", "ekstra-script", "icerik"}
ETIKET_DESEN = re.compile(r"^@([\w-]+):[ \t]*(.*)$", re.M)


def etiketleri_oku(kaynak):
    """
    Sayfa kaynağını @anahtar: bloklarına böler.
    Her bloğun değeri, bir sonraki geçerli @anahtar: satırına kadar sürer
    (yoksa dosya sonuna kadar). Sadece beyaz listedeki anahtarlar sayılır;
    @ikon: / @altin: gibi içerik işaretleri bölmeyi kesmez.
    """
    isaretler = [m for m in ETIKET_DESEN.finditer(kaynak) if m.group(1) in ETIKETLER]
    cikti = {}
    for i, m in enumerate(isaretler):
        bas = m.end()
        son = isaretler[i + 1].start() if i + 1 < len(isaretler) else len(kaynak)
        cikti[m.group(1)] = kaynak[bas:son].strip()
    return cikti


def kur():
    sablon = open(os.path.join(SRC, "sablon.html"), encoding="utf-8").read()
    surum = "0.1.0"
    vp = os.path.join(KOK, "VERSIYON.txt")
    if os.path.exists(vp):
        surum = open(vp, encoding="utf-8").read().strip()

    yazilan = []
    for dosya in sorted(os.listdir(SAYFA)):
        if not dosya.endswith(".html"):
            continue
        kaynak = open(os.path.join(SAYFA, dosya), encoding="utf-8").read()
        e = etiketleri_oku(kaynak)

        omurga_jp, bolum_ad = OMURGA_AD.get(dosya, ("", dosya.replace(".html", "")))

        cikti = sablon
        for anahtar, deger in {
            "BASLIK": e.get("baslik", dosya.replace(".html", "")),
            "ACIKLAMA": e.get("aciklama", ""),
            "EXTRA_KOPKA": e.get("ekstra-kopka", ""),
            "EXTRA_SCRIPT": e.get("ekstra-script", ""),
            "ICERIK": e.get("icerik", ""),
            "MENU": menu_html(dosya),
            "OMURGA_JP": omurga_jp,
            "BOLUM_AD": bolum_ad,
            "FOLYO": e.get("folio", ""),
            "MUHUR": altin_svg("altin"),
            "CEMBER": buyulu_cember("cember"),
            "ALT_MENU": alt_menu(),
            "YIL": "2026",
            "SURUM": surum,
        }.items():
            cikti = cikti.replace("{" + anahtar + "}", deger)

        if "{" in cikti:
            kalan = set(re.findall(r"\{([A-Z_ÇĞİÖŞÜ0-9]+)\}", cikti))
            if kalan:
                print("  ! çözülmeyen etiket:", sorted(kalan), dosya)

        cikti = temizle(cikti)
        hedef = os.path.join(KOK, dosya)
        open(hedef, "w", encoding="utf-8").write(cikti)
        yazilan.append((dosya, len(cikti)))

    print(f"{len(yazilan)} sayfa üretildi:")
    for d, n in yazilan:
        print(f"  {d:24s} {n//1024:4d} KB")


if __name__ == "__main__":
    os.makedirs(SAYFA, exist_ok=True)
    kur()