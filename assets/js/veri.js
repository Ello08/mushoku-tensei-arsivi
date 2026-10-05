/* ==========================================================================
   VERİ KATMANI
   Fandom'dan çekilmiş JSON'ları yükler; sayfalar bunları render eder.
   Prototip notu: içerik %100 buradan gelir, HTML'de sabit metin yoktur.
   ========================================================================== */

window.MT_VERI = (function () {
  const taban = "assets/data/";
  const onbellek = {};
  const yukle = (ad) => {
    if (!onbellek[ad]) {
      onbellek[ad] = fetch(taban + ad + ".json")
        .then((r) => {
          if (!r.ok) throw new Error(ad + " yüklenemedi (" + r.status + ")");
          return r.json();
        })
        .catch((e) => {
          console.error("[MT]", e);
          return null;
        });
    }
    return onbellek[ad];
  };

  return {
    anime: () => yukle("anime"),
    manga: () => yukle("manga"),
    novel: () => yukle("novel"),
    karakterler: () => yukle("karakterler"),
    yaylar: () => yukle("yaylar"),
    dunya: () => yukle("dunya"),
    temalar: () => yukle("temalar"),
    ekMedya: () => yukle("ek-medya"),
  };
})();

/* ---------------------------------------------------------------- yardımcı */

function el(tag, sinif, metin) {
  const n = document.createElement(tag);
  if (sinif) n.className = sinif;
  if (metin != null) n.textContent = metin;
  return n;
}

function ikon(ad, sinif) {
  const s = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  s.setAttribute("class", "ikon" + (sinif ? " " + sinif : ""));
  s.setAttribute("aria-hidden", "true");
  const u = document.createElementNS("http://www.w3.org/2000/svg", "use");
  u.setAttribute("href", "#i-" + ad);
  s.appendChild(u);
  return s;
}

/* "July 04, 2026" → "4 Tem 2026" (yoksa olduğu gibi döner) */
const AYLAR = {
  January: "Oca", February: "Şub", March: "Mar", April: "Nis", May: "May",
  June: "Haz", July: "Tem", August: "Ağu", September: "Eyl", October: "Eki",
  November: "Kas", December: "Ara",
};
function tarih(t) {
  if (!t) return "";
  const m = /([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})/.exec(t);
  if (!m) return t.trim();
  return parseInt(m[2], 10) + " " + (AYLAR[m[1]] || m[1]) + " " + m[3];
}

function kanit(metin, renk, ikonAd) {
  const s = el("span", "kanit" + (renk ? " " + renk : ""));
  s.appendChild(ikon(ikonAd || "kanit"));
  s.appendChild(el("span", null, metin));
  return s;
}

function bosDurum(mesaj) {
  const d = el("div", "nota");
  d.appendChild(ikon("uyari"));
  d.appendChild(el("div", null, mesaj));
  return d;
}

/* ---------------------------------------------------------------- BÖLÜMLER */

function bolumListesi(kap, dizi, secenek) {
  secenek = secenek || {};
  kap.innerHTML = "";
  if (!dizi || !dizi.length) {
    kap.appendChild(bosDurum("Bu veri kümesinde kayıt yok."));
    return;
  }
  const ul = el("ul", "sira");
  dizi.forEach((b) => {
    const li = el("li");

    const no = el("div", "sira-no", secenek.onebaslik ? b.no : "B" + b.no);
    if (b.ova) {
      const s = el("small", null, "OVA");
      no.appendChild(s);
    }
    li.appendChild(no);

    const govde = el("div");
    const ad = el("div", "sira-ad");
    ad.appendChild(document.createTextNode(b.baslik));
    if (b.jp) {
      const j = el("span", "jp jp-metni", "  " + b.jp);
      j.style.color = "var(--mana)";
      j.style.fontSize = ".82em";
      j.style.marginLeft = ".5rem";
      ad.appendChild(j);
    }
    govde.appendChild(ad);

    if (b.yay) {
      const y = el("div", "etiketler");
      y.style.marginTop = ".3rem";
      y.appendChild(etiket(b.yay, "bakir", "katlanir"));
      govde.appendChild(y);
    }
    if (b.ozet && secenek.ozet !== false) {
      govde.appendChild(el("p", "sira-ozet", b.ozet));
    }
    if (secenek.kanitlar !== false) {
      const k = el("div", "kanitler");
      k.style.marginTop = ".55rem";
      if (b.kaynak) k.appendChild(kanit(b.kaynak, "mana", "kitapacik"));
      if (b.acilis) k.appendChild(kanit("OP: " + b.acilis, null, "muzik"));
      if (b.kapanis) k.appendChild(kanit("ED: " + b.kapanis, null, "not"));
      if (k.children.length) govde.appendChild(k);
    }
    li.appendChild(govde);

    const sag = el("div", "sira-sag");
    if (b.yayinJp) sag.appendChild(el("div", null, tarih(b.yayinJp)));
    if (b.sayfa) sag.appendChild(el("div", "soluk", b.sayfa + " sf"));
    li.appendChild(sag);

    ul.appendChild(li);
  });
  kap.appendChild(ul);
}

function etiket(metin, renk, ikonAd) {
  const s = el("span", "etiket" + (renk ? " " + renk : ""));
  if (ikonAd) s.appendChild(ikon(ikonAd));
  s.appendChild(el("span", null, metin));
  return s;
}

/* ---------------------------------------------------------------- KARAKTERLER */

function karakterListesi(kap, dizi, grupFiltresi) {
  const sec = grupFiltresi;
  let goster = dizi;
  if (sec && sec.value) goster = dizi.filter((k) => k.grup === sec.value);

  const sayac = document.getElementById("kisi-sayac");
  if (sayac) sayac.textContent = goster.length + " kişi";

  kap.innerHTML = "";
  if (!goster.length) {
    kap.appendChild(bosDurum("Bu grupta kayıt yok."));
    return;
  }
  goster.forEach((k) => {
    const a = el("article", "kisi");
    const ust = el("div", "kisi-ust");
    const basHarf = k.ad.replace(/ Greyrat$/, "").replace(/^./, "");
    ust.appendChild(el("div", "mühür " + (k.ton || ""), basHarf.slice(0, 2).toUpperCase()));

    const kim = el("div");
    const h = el("h3");
    const bag = el("a", null, k.ad.replace(/ Greyrat$/, ""));
    bag.href = k.wiki;
    bag.target = "_blank";
    bag.rel = "noopener noreferrer";
    h.appendChild(bag);
    kim.appendChild(h);
    if (k.jp) kim.appendChild(el("div", "jp-ad jp jp-metni", k.jp));
    ust.appendChild(kim);
    a.appendChild(ust);

    if (k.ozet) a.appendChild(el("p", null, k.ozet));

    const alt = el("div", "kisi-alt");
    alt.appendChild(etiket(k.grup, k.grup === "Antagonist" ? "kizil" : null, "kalkan"));
    const w = el("a", "kanit");
    w.appendChild(ikon("dis"));
    w.appendChild(el("span", null, "wiki"));
    w.href = k.wiki;
    w.target = "_blank";
    w.rel = "noopener noreferrer";
    alt.appendChild(w);
    a.appendChild(alt);

    kap.appendChild(a);
  });
}

/* ---------------------------------------------------------------- KONU / DÜNYA */

function konuListesi(kap, dizi) {
  kap.innerHTML = "";
  if (!dizi || !dizi.length) {
    kap.appendChild(bosDurum("Konu kaydı yok."));
    return;
  }
  dizi.forEach((c) => {
    const d = el("details", "detay");
    const s = el("summary");
    s.appendChild(ikon("ok"));
    s.appendChild(el("span", null, c.ad));
    if (c.tur) {
      const t = el("span", "etiket" + (c.tur.length > 2 ? " soluk" : " bakir"), c.tur);
      t.style.marginLeft = "auto";
      s.appendChild(t);
    }
    d.appendChild(s);
    const g = el("div", "govde");
    g.appendChild(el("p", null, c.ozet));
    (c.bolumler || []).forEach((b) => {
      g.appendChild(el("h3", null, b.ad));
      g.appendChild(el("p", "zayif", b.metin));
    });
    const w = el("a", "kanit");
    w.href = c.wiki;
    w.target = "_blank";
    w.rel = "noopener noreferrer";
    w.style.marginTop = ".6rem";
    w.appendChild(ikon("dis"));
    w.appendChild(el("span", null, "Fandom sayfası"));
    g.appendChild(w);
    d.appendChild(g);
    kap.appendChild(d);
  });
}

/* ---------------------------------------------------------------- YAYLAR */

function yayListesi(kap, dizi) {
  kap.innerHTML = "";
  let sonGrup = null;
  (dizi || []).forEach((y) => {
    if (y.part !== sonGrup) {
      sonGrup = y.part;
      const h = el("h3", "no", sonGrup);
      h.style.marginTop = "2.4rem";
      h.style.marginBottom = ".3rem";
      kap.appendChild(h);
    }
    const det = el("details", "detay");
    const s = el("summary");
    s.appendChild(ikon("ok"));
    s.appendChild(el("span", null, y.ad));
    det.appendChild(s);
    const g = el("div", "govde");
    g.appendChild(el("p", null, y.ozet));
    det.appendChild(g);
    kap.appendChild(det);
  });
}

/* ---------------------------------------------------------------- genel API
   Sayfalar bu yüzeyi kullanır. Yeni bir medya kolu eklemek için:
   1) assets/data/<kol>.json üret
   2) MT_VERI.<kol>() ekle
   3) Buraya bir render fonksiyonu yaz ve MT_UI'ye ekle           */

window.MT_UI = {
  el,
  ikon,
  tarih,
  etiket,
  kanit,
  bosDurum,
  bolumListesi,
  karakterListesi,
  konuListesi,
  yayListesi,
};

/* ---------------------------------------------------------------- ARAMA */

window.MT_ARAMA = (function () {
  let indeks = null;
  let aktif = -1;
  let sonuc = [];

  function kisa(metin, n) {
    metin = (metin || "").replace(/\s+/g, " ").trim();
    return metin.length > n ? metin.slice(0, n) + "…" : metin;
  }

  function kucukHarf(s) {
    return (s || "").toLocaleLowerCase("tr");
  }

  function vurgula(metin, q) {
    const d = document.createElement("div");
    const i = kucukHarf(metin).indexOf(kucukHarf(q));
    if (i < 0) { d.textContent = metin; return d; }
    d.appendChild(document.createTextNode(metin.slice(0, i)));
    const m = document.createElement("mark");
    m.textContent = metin.slice(i, i + q.length);
    d.appendChild(m);
    d.appendChild(document.createTextNode(metin.slice(i + q.length)));
    return d;
  }

  async function kur() {
    if (indeks) return indeks;
    const [a, m, n, k, y, d, t, e] = await Promise.all([
      MT_VERI.anime(), MT_VERI.manga(), MT_VERI.novel(), MT_VERI.karakterler(),
      MT_VERI.yaylar(), MT_VERI.dunya(), MT_VERI.temalar(), MT_VERI.ekMedya(),
    ]);
    indeks = [];

    /* Serinin kendisi: takma adlar ve ana başlıklar */
    indeks.push({
      tur: "seri",
      ad: "Mushoku Tensei: ~Isekai Ittara Honki Dasu~",
      detay: "Dizinin kendisi · 2012'den beri yayınlanıyor",
      yol: "index.html",
      arama: kucukHarf(
        "mushoku tensei mushoku tensei isekai ittara honki dasu jobless reincarnation " +
        "無職転生 異世界行ったら本気だす rifujin na magonote shirotaka isekai " +
        "anime manga novel web novel light novel quiz ansiklopedi arsiv " +
        "paul ruders greyrat eris boreas greyrat roxy migurdia sylphiette orsted " +
        "hitogami laplace ruijerd superdia zanoba shirone"
      ),
    });

    (a && a.episodes || []).forEach((b) =>
      indeks.push({
        tur: "anime", ad: b.baslik + (b.jp ? " (" + b.jp + ")" : ""),
        detay: "Sezon " + b.sezon + " Bölüm " + b.no + " · " + (b.yay || "") + " · " + tarih(b.airJp),
        yol: "anime.html#s" + b.sezon + "e" + String(b.no).replace(".", ""),
        ana: (b.baslik + " " + b.jp + " " + b.yay + " " + b.ozet + " " + (b.kaynak || "")),
      })
    );
    (m && m.ana || []).forEach((c) =>
      indeks.push({
        tur: "manga", ad: "Cilt " + c.no + " — " + c.baslik.replace(/^Cilt \d+ — /, ""),
        detay: "Yuka Fujikawa · " + tarih(c.yayinJp) + (c.sayfa ? " · " + c.sayfa + " sayfa" : ""),
        yol: "manga.html#cilt-" + c.no,
        ana: (c.baslik + " " + c.ozet + " " + (c.yazar || "") + " " + (c.cizgi || "")),
      })
    );
    (n && n.lightNovel || []).forEach((c) =>
      indeks.push({
        tur: "novel", ad: "Light Novel Cilt " + c.no + (c.arc ? " — " + c.arc : ""),
        detay: "Rifujin na Magonote · " + tarih(c.yayinJp),
        yol: "novel.html#cilt-" + c.no,
        ana: c.baslik + " " + c.ozet + " " + (c.arc || ""),
      })
    );
    (k && k.karakterler || []).forEach((p) =>
      indeks.push({
        tur: "karakter", ad: p.ad.replace(/ Greyrat$/, ""),
        detay: p.grup + " · " + kisa(p.ozet, 70),
        yol: "karakterler.html?" + encodeURIComponent(p.ad.replace(/ Greyrat$/, "")),
        ana: p.ad + " " + p.grup + " " + p.ozet,
      })
    );
    (y && y.yaylar || []).forEach((v) =>
      indeks.push({
        tur: "yay", ad: v.ad, detay: v.part + " · " + kisa(v.ozet, 70),
        yol: "yaylar.html", ana: v.ad + " " + v.ozet,
      })
    );
    (d && d.konular || []).forEach((v) =>
      indeks.push({
        tur: "dunya", ad: v.ad, detay: kisa(v.ozet, 70), yol: "dunya.html",
        ana: v.ad + " " + v.ozet + " " + (v.bolumler || []).map((x) => x.ad + " " + x.metin).join(" "),
      })
    );
    (t && t.kavramlar || []).forEach((v) =>
      indeks.push({
        tur: "kavram", ad: v.ad, detay: kisa(v.ozet, 70), yol: "analiz.html",
        ana: v.ad + " " + v.ozet,
      })
    );
    (e && e.kayitlar || []).forEach((v) =>
      indeks.push({
        tur: "ek", ad: v.ad, detay: v.tur + " · " + kisa(v.ozet, 60),
        yol: "medya-eklenti.html", ana: v.ad + " " + v.ozet,
      })
    );
    indeks.forEach((x) => { if (!x.arama) x.arama = kucukHarf((x.ana || "") + " " + x.ad); });
    return indeks;
  }

  const TUR_IKON = {
    seri: "efsane", anime: "film", manga: "kitap", novel: "kalem",
    karakter: "kilic", yay: "katlanir", dunya: "harita", kavram: "goz",
    ek: "disk",
  };

  /* Levenshtein — yalnızca kısa sorgularda, küçük toleransla */
  function mesafe(a, b, enFazla) {
    if (Math.abs(a.length - b.length) > enFazla) return enFazla + 1;
    let onceki = Array.from({ length: b.length + 1 }, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
      const simdi = [i];
      let enKucuk = i;
      for (let j = 1; j <= b.length; j++) {
        const maliyet = onceki[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1);
        simdi[j] = Math.min(onceki[j] + 1, simdi[j - 1] + 1, maliyet);
        if (simdi[j] < enKucuk) enKucuk = simdi[j];
      }
      if (enKucuk > enFazla) return enFazla + 1;
      onceki = simdi;
    }
    return onceki[b.length];
  }

  /* Sorgu terimini arama metnine " yamultarak" eşleştir:
     yalnızca kısa terimlerde (yazım hatası toleransı). */
  function bulanikEslesir(terim, aramaMetni) {
    const t = kucukHarf(terim);
    if (t.length < 4 || t.length > 12) return false;
    const tolerans = t.length <= 5 ? 1 : 2;
    const parcalar = aramaMetni.split(/[^a-z0-9çğıöşüâîû]+/);
    return parcalar.some((p) => p.length >= 3 && p.length <= t.length + tolerans &&
      mesafe(p, t, tolerans) <= tolerans);
  }

  function ara(q) {
    const temiz = kucukHarf(q).trim();
    if (temiz.length < 2) { sonuc = []; return []; }
    const parcalar = temiz.split(/\s+/);
    const sirasir = (a, b) => {
      const ai = a.ad.toLocaleLowerCase("tr").startsWith(temiz) ? 0 : 1;
      const bi = b.ad.toLocaleLowerCase("tr").startsWith(temiz) ? 0 : 1;
      return ai - bi || a.ad.length - b.ad.length;
    };
    let bulunan = indeks.filter((x) => parcalar.every((p) => x.arama.includes(p)));
    /* Tam eşleşme az sonuç verirse yazım hatası toleransı */
    if (bulunan.length < 5) {
      const yakin = indeks.filter((x) => !bulunan.includes(x) &&
        parcalar.every((p) => bulanikEslesir(p, x.arama)));
      bulunan = bulunan.concat(yakin);
    }
    sonuc = bulunan.sort(sirasir).slice(0, 40);
    return sonuc;
  }

  function ciz(kap, q) {
    kap.innerHTML = "";
    sonuc.forEach((r, i) => {
      const a = el("a", "sonuc" + (i === aktif ? " secili" : ""));
      a.href = r.yol;
      a.appendChild(ikon(TUR_IKON[r.tur] || "nokta"));
      const g = el("div");
      const b = el("b");
      b.appendChild(vurgula(r.ad, q.trim()));
      g.appendChild(b);
      g.appendChild(el("span", null, r.detay));
      a.appendChild(g);
      kap.appendChild(a);
    });
  }

  function hareket(yon) {
    if (!sonuc.length) return;
    aktif = Math.max(0, Math.min(sonuc.length - 1, aktif + yon));
    ciz(document.getElementById("arama-sonuc"), document.getElementById("arama-girdi").value);
    const s = document.querySelector(".sonuc.secili");
    if (s) s.scrollIntoView({ block: "nearest" });
  }

  async function ac() {
    const kat = document.getElementById("arama-kat");
    kat.classList.add("acik");
    document.body.style.overflow = "hidden";
    const g = document.getElementById("arama-girdi");
    g.focus();
    g.select();
    await kur();
  }

  function kapat() {
    document.getElementById("arama-kat").classList.remove("acik");
    document.body.style.overflow = "";
    aktif = -1;
  }

  function bagla() {
    const kat = document.getElementById("arama-kat");
    if (!kat) return;
    const g = document.getElementById("arama-girdi");
    const kap = document.getElementById("arama-sonuc");

    g.addEventListener("input", () => { aktif = -1; ara(g.value); ciz(kap, g.value); });
    g.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { e.preventDefault(); hareket(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); hareket(-1); }
      else if (e.key === "Enter" && sonuc[aktif]) { e.preventDefault(); location.href = sonuc[aktif].yol; }
    });
    kat.addEventListener("click", (e) => { if (e.target === kat) kapat(); });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && kat.classList.contains("acik")) kapat();
      const y = e.key.toLowerCase();
      if ((e.ctrlKey || e.metaKey) && y === "k") { e.preventDefault(); kat.classList.contains("acik") ? kapat() : ac(); }
      if (e.key === "/" && document.activeElement.tagName !== "INPUT" && !kat.classList.contains("acik")) {
        e.preventDefault(); ac();
      }
    });
    document.querySelectorAll("[data-arama-ac]").forEach((b) =>
      b.addEventListener("click", (e) => { e.preventDefault(); ac(); })
    );
    document.querySelectorAll("[data-arama-kapat]").forEach((b) =>
      b.addEventListener("click", kapat)
    );
  }

  return {
    bagla,
    ac,
    kapat,
    hazirla: kur,      // indeksi kur (sayfa açılışında çağrılır)
    ara,               // arama (diz döner)
    boyut: () => (indeks ? indeks.length : 0),
  };
})();