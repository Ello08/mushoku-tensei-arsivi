# Mushoku Tensei Ansiklopedisi

*無職転生 〜異世界行ったら本気だす〜* üzerine Türkçe bir hayran ansiklopedisi.

**Canlı:** https://ello08.github.io/mushoku-tensei-arsivi/

## Ne içerir

| Kanal | İçerik | Kaynak |
|---|---|---|
| **Anime** | 3 sezon · 62 bölüm; tarih, açılış/kapanış müziği, senaryo, uyarlama kaynağı | Fandom |
| **Manga** | 25 ana cilt + 22 yan seri (4-Koma, Eris Gaiden, Roxy Gets Serious, Depressed Magician, Antoloji) | Fandom |
| **Novel** | 26 light novel cilt + web novel + 6 ek kitap | Fandom + Wikipedia |
| **Karakterler** | 66 kayıt, 17 gruba göre süzgeçlenebilir | Fandom |
| **Dünya** | 45 sistem kaydı: ırklar, büyü, kılıç stilleri, Yedi Büyük Güç | Fandom |
| **Yaylar** | 23 anlatı yayı, özetleriyle | Fandom |
| **Analiz** | 8 uzun tematik okuma (site özgünü) | — |
| **Rehber** | Medya seçimi, içerik uyarıları, yaygın yanlışlar | — |

## Prototip mimarisi

Tüm listeler **veri katmanından** beslenir; HTML'de sabit kayıt yoktur.

```
src/sablon.html      ortak iskelet (üst çubuk, arama, alt bilgi, dikey omurga)
src/sayfa/*.html     sayfa içerikleri (@baslik:, @icerik: blokları)
        │
        │  python3 tools/kur.py
        ▼
*.html                statik çıktı (depoda tutulur)
        │
        │  tarayıcıda fetch()
        ▼
assets/data/*.json   anime · manga · novel · karakterler · yaylar · dunya · temalar · ek-medya
```

Veri akışı:

```
fandom API ──► tools/veri-cek.py ──► tools/ham/raw/pages.json
                                            │
                                            │  python3 tools/build_data.py
                                            ▼
                                     assets/data/*.json
```

## Geliştirme

```bash
python3 tools/kur.py        # src → site
python3 tools/dogrula.py    # bağlantı, çapa, HTML, ikon, erişilebilirlik
node    tools/test-veri.js  # veri katmanı duman testi (Node 18+)

python3 -m http.server 8000 # yerelde önizleme
```

Veriyi tamamen yenilemek için (ağ gerekir):

```bash
python3 tools/veri-cek.py
python3 tools/build_data.py
python3 tools/kur.py
```

## Yeni medya kolu ekleme

1. `tools/build_data.py` içine JSON üretimini ekle
2. `assets/js/veri.js` → `MT_VERI` sözlüğüne yükleme fonksiyonu ekle
3. `src/sayfa/<kol>.html` yaz
4. `tools/kur.py` → `MENU` listesine ekle
5. `python3 tools/kur.py && python3 tools/dogrula.py`

## Tasarım

Palet keyfi seçilmedi; her vurgu rengi dünyadaki bir şeye bağlı.

| Renk | Kaynak | Anlam |
|---|---|---|
| Migurd mavisi | Roxy | bilgi, olgu |
| Boreas kızılı | Eris | arzu, uyarı |
| Büyük Orman yeşili | Sylphie | sıradan hayat |
| Kılıç Tanrısı altını | Paul | yapı, kanıt |
| Boşluk Dünyası moru | Hitogami | spoiler, kâhinlik |
| Sharia gece mavisi | dünya | zemin |

İmza motifi **Altı Yüzlü Dünya** (vesica piscis) — iki üst üste binen daire.

## CI/CD

`.github/workflows/deploy.yml` — push'ta önce doğrulama, sonra GitHub Pages.

`dogrula` işi: sayfaları üretir, üretilen HTML'nin depoda yazan sürümle aynı
olduğunu denetler, bağlantı/çapa/HTML/ikon denetimini çalıştırır, veri katmanı
testini koşturur. Hepsi geçerse `yayinla` işi Pages'e dağıtır.

## Haklar

Fan projesidir, **resmî değildir**. Tüm haklar Rifujin na Magonote, Shirotaka,
Media Factory, Studio Bind ve ilgili yapımlara aittir. Kapak görseli, afiş veya
karakter resmi kullanılmaz; görseller bu repo için üretilmiş geometrik
işaretlerdir. Kaynak: [mushokutensei.fandom.com](https://mushokutensei.fandom.com/).
