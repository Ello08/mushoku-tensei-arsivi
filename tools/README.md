# tools/

Prototipin üretim ve doğrulama araçları. Üretim çıktısı (`*.html`)
depoda tutulur; `src/` ve `assets/data/` kaynaklardır.

| Dosya | Ne yapar |
|---|---|
| `veri-cek.py` | Fandom MediaWiki API'sinden ham wikitext çeker, `tools/ham/raw/pages.json` üretir. |
| `build_data.py` | Ham wikitext → `assets/data/*.json` (veri katmanı). |
| `kur.py` | `src/sablon.html` + `src/sayfa/*.html` → site kökündeki `*.html`. |
| `dogrula.py` | Bağlantı, çapa, HTML kapanışları, ikon bütünlüğü, erişilebilirlik denetimi. |
| `test-veri.js` | Veri katmanı duman testi (Node, tarayıcısız). |

## Yeniden üretim

```bash
python3 tools/veri-cek.py     # ağ: fandom'den ham veri (isteğe bağlı)
python3 tools/build_data.py   # ham → assets/data
python3 tools/kur.py          # src → site
python3 tools/dogrula.py      # doğrula
node    tools/test-veri.js    # veri katmanı testi
```

## Yeni medya kolu eklemek

1. `tools/build_data.py` içine yeni JSON üretimini ekle.
2. `assets/js/veri.js` → `MT_VERI` sözlüğüne yükleme fonksiyonu ekle.
3. `src/sayfa/<kol>.html` yaz; `tools/kur.py` içindeki `MENU` listesine ekle.
4. `tools/dogrula.py` çalıştır.
