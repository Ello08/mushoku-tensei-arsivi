/**
 * Veri katmanı duman testi (Node ortamı, tarayıcısız).
 * window/document/fetch taklitleriyle bölüm listesi, karakter süzgeci,
 * arama indeksi ve konu listelerini çalıştırır.
 */
const fs = require("fs");
const path = require("path");
const KOK = path.resolve(__dirname, "..");

let hata = 0;
const ok = (m) => console.log("  ✓ " + m);
const ko = (m) => { console.log("  ✗ " + m); hata++; };

/* ---------------------------------------------------------- DOM taklidi */
class El {
  constructor(tag) {
    this.tagName = (tag || "").toUpperCase();
    this.children = [];
    this.attributes = {};
    this.className = "";
    this.style = {};
    this.dataset = {};
    this.text = "";
    this.hidden = false;
    this._html = null;
    this.classList = {
      _k: new Set(),
      add: (c) => this.classList._k.add(c),
      remove: (c) => this.classList._k.delete(c),
      toggle: (c, z) => (z === undefined ? (this.classList._k.has(c) ? this.classList._k.delete(c) : this.classList._k.add(c)) : (z ? this.classList._k.add(c) : this.classList._k.delete(c))),
      contains: (c) => this.classList._k.has(c),
    };
  }
  select() {}
  focus() {}
  set className(v) { this.attributes.class = v; this._class = v; }
  get className() { return this._class || ""; }
  set innerHTML(v) { this._html = v; if (v === "") this.children = []; }
  get innerHTML() { return this._html; }
  set textContent(v) { this.text = v; this.children = []; }
  get textContent() {
    return this.text || this.children.map((c) => c.textContent || "").join("");
  }
  appendChild(c) { this.children.push(c); return c; }
  insertBefore(c) { this.children.unshift(c); return c; }
  setAttribute(k, v) { this.attributes[k] = v; if (k === "class") this._class = v; }
  getAttribute(k) { return this.attributes[k] || null; }
  addEventListener() {}
  querySelector() { return null; }
  querySelectorAll() { return []; }
  get firstChild() { return this.children[0] || null; }
  click() {}
}

const KIMLIK = {
  "arama-kat": new El("div"),
  "arama-girdi": Object.assign(new El("input"), { value: "" }),
  "arama-sonuc": new El("div"),
};

const BELGE = {
  createElement: (t) => new El(t),
  createElementNS: (ns, t) => new El(t),
  createTextNode: (t) => { const e = new El("#text"); e.text = t; return e; },
  querySelector: (q) => (q.startsWith("#") ? KIMLIK[q.slice(1)] || null : null),
  querySelectorAll: () => [],
  getElementById: (id) => KIMLIK[id] || null,
  addEventListener: () => {},
  body: new El("body"),
  documentElement: new El("html"),
};

global.window = global;
global.document = BELGE;
global.localStorage = { getItem: () => null, setItem: () => {} };
global.location = { search: "", hash: "" };
global.navigator = { userAgent: "node" };
global.requestAnimationFrame = (f) => f();

/* fetch taklidi: gerçek JSON dosyalarını oku */
global.fetch = (yol) =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve(
        JSON.parse(fs.readFileSync(path.join(KOK, yol), "utf-8"))
      ),
  });

/* ---------------------------------------------------------- yükle */
require(path.join(KOK, "assets/js/icons.js"));
require(path.join(KOK, "assets/js/veri.js"));

console.log("\n[1] ikon seti");
const sprite = BELGE.body.children[0];
const sembol = (sprite && sprite.innerHTML.match(/<symbol /g)) || [];
if (sembol.length === 59) ok(`${sembol.length} sembol üretildi`);
else ko(`sembol sayısı ${sembol.length} (beklenen 59)`);

const kisa = (t, n = 68) => (t && t.length > n ? t.slice(0, n) + "…" : t || "");

console.log("\n[2] anime bölüm listesi");
MT_VERI.anime().then((v) => {
  if (!v) return ko("anime.json yüklenemedi");

  const sezonlar = v.seasons.length;
  ok(`${sezonlar} sezon, ${v.episodes.length} bölüm yüklendi`);

  for (const s of v.seasons) {
    const kok = new El("div");
    MT_UI.bolumListesi(kok, s.bolumler, { onebaslik: true });
    const ul = kok.children[0];
    const satir = ul && ul.children[0];
    if (ul && ul.children.length === s.bolumler.length && satir && satir.children.length === 3)
      ok(`S${s.key}: ${ul.children.length} satır, her satırda 3 kolon`);
    else ko(`S${s.key}: ${ul ? ul.children.length : 0} satır — beklenen ${s.bolumler.length}`);
  }

  // alan doluluk oranı
  const eksik = v.episodes.filter(
    (b) => !b.baslik || !b.airJp || !b.yay
  );
  if (eksik.length === 0) ok("tüm bölümlerde başlık, tarih ve yay alanı dolu");
  else ko(`${eksik.length} bölümde eksik alan: ${kisa(eksik.map((e) => e.no).join(","))}`);

  const ova = v.episodes.filter((b) => b.ova);
  if (ova.length === 1) ok(`OVA ayrı işaretlendi: S${ova[0].sezon} · ${ova[0].baslik}`);
  else ko(`OVA sayısı ${ova.length} (beklenen 1)`);

  console.log("\n[3] manga / novel");
  return Promise.all([MT_VERI.manga(), MT_VERI.novel()]).then(([m, n]) => {
    const mk = new El("div");
    MT_UI.bolumListesi(mk, m.ana, { onebaslik: true });
    ok(`manga: ${m.ana.length} ana cilt + ${m.yan.length} yan seri`);
    const nk = new El("div");
    MT_UI.bolumListesi(nk, n.lightNovel, { onebaslik: true });
    ok(`novel: ${n.lightNovel.length} light novel + ${n.webNovel.length} web + ${n.ekstra.length} ek cilt`);

    const ciltler = n.lightNovel.filter((c) => c.arc).length;
    if (ciltler >= 20) ok(`${ciltler} ciltte yay eşleştirmesi var`);
    else ko(`yay eşleştirmesi zayıf: ${ciltler}/26`);

    console.log("\n[4] karakterler");
    return MT_VERI.karakterler();
  })
    .then((k) => {
      const kap = new El("div");
      MT_UI.karakterListesi(kap, k.karakterler, null);
      const uretilen = kap.children.length;
      if (uretilen === k.karakterler.length) ok(`${uretilen} kart üretildi`);
      else ko(`${uretilen} kart, beklenen ${k.karakterler.length}`);

      const gruplu = {};
      k.karakterler.forEach((x) => { gruplu[x.grup] = (gruplu[x.grup] || 0) + 1; });
      ok("gruplar: " + Object.entries(gruplu).map(([a, b]) => `${a}=${b}`).join(", "));

      const ana = k.karakterler.filter((x) => x.grup === "Ana");
      if (ana.length >= 4) ok(`${ana.length} ana karakter mevcut`);
      else ko(`ana karakter eksik: ${ana.length}`);

      console.log("\n[5] dünya / kavram");
      return Promise.all([MT_VERI.dunya(), MT_VERI.temalar(), MT_VERI.yaylar(), MT_VERI.ekMedya()]);
    })
    .then(([d, t, y, e]) => {
      const dk = new El("div");
      MT_UI.konuListesi(dk, d.konular);
      ok(`${d.konular.length} dünya konusu`);
      const tk = new El("div");
      MT_UI.konuListesi(tk, t.kavramlar);
      ok(`${t.kavramlar.length} kavram kaydı`);
      const yk = new El("div");
      MT_UI.yayListesi(yk, y.yaylar);
      ok(`${y.yaylar.length} anlatı yayı`);
      const ek = new El("div");
      MT_UI.konuListesi(ek, e.kayitlar);
      ok(`${e.kayitlar.length} ek medya kaydı`);

      const parca = y.yaylar.filter((a) => a.ozet && a.ozet.length > 120).length;
      if (parca === y.yaylar.length) ok("tüm yaylarda 120+ karakter özet var");
      else ko(`${y.yaylar.length - parca} yayda özet kısa/eksik`);

      console.log("\n[6] arama indeksi");
      return MT_ARAMA.hazirla().then((idx) => {
        ok(`${idx.length} kayıt indekslendi`);
        const turler = {};
        idx.forEach((x) => { turler[x.tur] = (turler[x.tur] || 0) + 1; });
        ok("tür dağılımı: " + Object.entries(turler).map(([a, b]) => `${a}=${b}`).join(", "));

        /* Sorgu -> bulunması gereken tür (birden fazla tür kabul edilir) */
        const sinamalar = [
          ["isekai", ["seri"]],
          ["無職転生", ["seri"]],
          ["mushoku tensei", ["seri"]],
          ["roxy", ["karakter"]],
          ["hitogami", ["kavram", "karakter"]],
          ["burn mad dog", ["anime"]],
          ["sword sanctuary", ["dunya", "karakter"]],
          ["cilt 12", ["manga", "novel"]],
          ["laplace", ["karakter", "kavram", "dunya"]],
          ["rnoa", ["anime"]],              // yazım hatası: "rnoa" -> "r anoa"
        ];
        sinamalar.forEach(([q, beklenenler]) => {
          const r = MT_ARAMA.ara(q);
          const turler = [...new Set(r.map((x) => x.tur))];
          const eslesti = turler.some((t) => beklenenler.includes(t));
          if (eslesti) ok(`"${q}" → ${r.length} sonuç [${turler.join(", ")}]`);
          else ko(`"${q}" → ${r.length} sonuç [${turler.join(", ") || "-"}], beklenen: ${beklenenler.join("/")}`);
        });

        const bos = MT_ARAMA.ara("xqzwvv");
        if (bos.length === 0) ok("anlamsız sorgu boş dönüyor");
        else ko(`anlamsız sorgu ${bos.length} sonuç döndürdü`);

        return MT_ARAMA.ac().then(() => {
          const kat = BELGE.getElementById("arama-kat");
          if (kat.classList.contains("acik")) ok("arama katmanı açılabiliyor");
          else ko("arama katmanı açılmadı");
        });
      });
    })
    .then(() => {
      console.log(hata === 0 ? "\nTEST TAMAM — hata yok" : `\nTEST BİTTİ — ${hata} hata`);
      process.exit(hata === 0 ? 0 : 1);
    })
    .catch((hata_) => {
      console.error("\nÇÖKME:", hata_);
      process.exit(1);
    });
});