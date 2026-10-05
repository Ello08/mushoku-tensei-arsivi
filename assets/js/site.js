/* ==========================================================================
   SİTE DAVRANIŞI
   tema · gezinme · arama · spoiler · sekme · süzgeç · görünürlük
   ========================================================================== */

(function () {
  const $ = (s, k) => (k || document).querySelector(s);
  const $$ = (s, k) => Array.from((k || document).querySelectorAll(s));

  /* ---------------------------------------------------------- 1. Tema */
  const ANAHTAR = "mt-tema";
  function temaUygula(t) {
    document.documentElement.setAttribute("data-tema", t);
    $$("[data-tema-dugme]").forEach((b) => {
      const koyu = t === "koyu";
      b.querySelector("use").setAttribute("href", koyu ? "#i-ay" : "#i-gunes");
      b.setAttribute("aria-label", koyu ? "Açık temaya geç" : "Koyu temaya geç");
    });
    $$("[data-tema-metin]").forEach((e) => (e.textContent = t === "koyu" ? "Gece" : "Parşömen"));
  }
  function temaTers() {
    return document.documentElement.getAttribute("data-tema") === "koyu" ? "pargamen" : "koyu";
  }
  const kayitli = (() => { try { return localStorage.getItem(ANAHTAR); } catch (e) { return null; } })();
  temaUygula(kayitli || "koyu");

  document.addEventListener("DOMContentLoaded", () => {
    $$("[data-tema-dugme]").forEach((b) =>
      b.addEventListener("click", () => {
        const t = temaTers();
        temaUygula(t);
        try { localStorage.setItem(ANAHTAR, t); } catch (e) {}
      })
    );
  });

  /* ---------------------------------------------------------- 2. Üst çubuk + ilerleme */
  const ilerleme = $(".ilerleme");
  const ust = $(".ust");
  const yukari = $(".yukari");
  let sonYukleme = -1;

  function kaydirma() {
    const y = window.scrollY || 0;
    const h = document.documentElement.scrollHeight - window.innerHeight;
    if (ilerleme) ilerleme.style.width = (h > 0 ? (y / h) * 100 : 0) + "%";
    if (ust) ust.classList.toggle("sikisik", y > 12);
    if (yukari) yukari.classList.toggle("acik", y > 700);
    const yeni = Math.floor(y);
    if (Math.abs(yeni - sonYukleme) > 120) {
      sonYukleme = yeni;
      belirGuncelle();
    }
  }
  let raf = null;
  window.addEventListener("scroll", () => {
    if (raf) return;
    raf = requestAnimationFrame(() => { kaydirma(); raf = null; });
  }, { passive: true });

  if (yukari) yukari.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));

  /* ---------------------------------------------------------- 3. Mobil menü */
  document.addEventListener("DOMContentLoaded", () => {
    const gez = $(".gezinme");
    const md = $(".menu-dugme");
    if (!gez || !md) return;
    md.addEventListener("click", () => {
      const acik = gez.classList.toggle("acik");
      md.setAttribute("aria-expanded", acik ? "true" : "false");
      md.querySelector("use").setAttribute("href", acik ? "#i-kapat" : "#i-menu");
    });
    $$(".gez", gez).forEach((a) =>
      a.addEventListener("click", () => {
        gez.classList.remove("acik");
        md.setAttribute("aria-expanded", "false");
        md.querySelector("use").setAttribute("href", "#i-menu");
      })
    );
  });

  /* ---------------------------------------------------------- 4. Görünürlük animasyonu */
  function belirGuncelle() {
    const yuk = window.innerHeight * 0.9;
    $$(".tut").forEach((n, i) => {
      const r = n.getBoundingClientRect();
      if (r.top > yuk || r.bottom < -100 || n.dataset.gordu) return;
      n.dataset.gordu = "1";
      n.style.setProperty("--gecikme", Math.min(i * 0.05, 0.5) + "s");
      n.classList.add("gorunur");
      if (n.tagName === "IMG") n.setAttribute("loading", "lazy");
    });
  }

  /* ---------------------------------------------------------- 5. Spoiler */
  document.addEventListener("DOMContentLoaded", () => {
    $$(".basin").forEach((n) =>
      n.addEventListener("click", () => {
        n.classList.toggle("acik");
        n.setAttribute("aria-expanded", n.classList.contains("acik") ? "true" : "false");
      })
    );
    $$(".perde").forEach((n) =>
      n.addEventListener("click", () => {
        n.classList.toggle("acik");
        const kilit = $(".kilit", n);
        if (kilit) kilit.setAttribute("aria-hidden", n.classList.contains("acik") ? "true" : "false");
      })
    );
    /* "tümünü göster" */
    $$("[data-spoiler-ac]").forEach((b) =>
      b.addEventListener("click", () => {
        $$(".basin, .perde", b.closest("section, .bolum") || document).forEach((n) => n.classList.add("acik"));
      })
    );
  });

  /* ---------------------------------------------------------- 6. Sekmeler */
  document.addEventListener("DOMContentLoaded", () => {
    $$("[data-sekmeler]").forEach((grup) => {
      const dugmeler = $$("[data-sekme]", grup);
      const panolar = $$("[data-panel]", grup.closest(".bolum, .defter") || document);
      function goster(anahtar) {
        dugmeler.forEach((d) => d.classList.toggle("aktif", d.dataset.sekme === anahtar));
        panolar.forEach((p) => (p.hidden = p.dataset.panel !== anahtar));
      }
      dugmeler.forEach((d) => d.addEventListener("click", () => goster(d.dataset.sekme)));
      if (dugmeler.length) goster(dugmeler[0].dataset.sekme);
    });
  });

  /* ---------------------------------------------------------- 6b. Kanal seçimi (rehber) */
  document.addEventListener("DOMContentLoaded", () => {
    const dugmeler = $$("[data-kanal]");
    if (!dugmeler.length) return;
    const panolar = $$("[data-kanal-panel]");
    function goster(k) {
      dugmeler.forEach((d) => d.classList.toggle("aktif", d.dataset.kanal === k));
      panolar.forEach((p) => (p.hidden = p.dataset.kanalPanel !== k));
    }
    dugmeler.forEach((d) => d.addEventListener("click", () => goster(d.dataset.kanal)));
    goster(dugmeler[0].dataset.kanal);
  });

  /* ---------------------------------------------------------- 7. Karakter filtresi
     Süzgeç düğmeleri karakterler.html tarafından veriden üretilir ve
     orada bağlanır; burada yalnız seçili grubu hatırlıyoruz. */

  /* ---------------------------------------------------------- 8. İçindekiler izleyici */
  document.addEventListener("DOMContentLoaded", () => {
    const ic = $(".dizin-ici");
    if (!ic) return;
    const baglar = $$("a[href^='#']", ic);
    if (!baglar.length) return;
    const hedefler = baglar
      .map((a) => document.getElementById(decodeURIComponent(a.getAttribute("href").slice(1))))
      .filter(Boolean);
    if (!hedefler.length) return;

    const gozlemci = new IntersectionObserver(
      (girisler) => {
        girisler.forEach((g) => {
          if (!g.isIntersecting) return;
          baglar.forEach((a) =>
            a.classList.toggle("aktif", a.getAttribute("href").slice(1) === g.target.id)
          );
        });
      },
      { rootMargin: "-20% 0px -70% 0px" }
    );
    hedefler.forEach((h) => gozlemci.observe(h));
  });

  /* ---------------------------------------------------------- 9. İkon kısayolu */
  document.addEventListener("DOMContentLoaded", () => {
    if (window.mtIkonla) window.mtIkonla(document);
    kaydirma();
    belirGuncelle();
  });
  document.addEventListener("scroll", belirGuncelle, { passive: true });
  window.addEventListener("resize", belirGuncelle, { passive: true });
})();