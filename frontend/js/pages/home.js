import { get } from "../shared/api.js";
import {
  bindProductCardActions,
  createSkeletonCards,
  initSite,
  productCardMarkup,
  startProgress,
  endProgress,
} from "../shared/site.js";

/* ─── Hero Slider ─── */
function initHeroSlider() {
  const slides = document.querySelectorAll(".hero-slide");
  const dots   = document.querySelectorAll(".hero-dot");
  const prev   = document.querySelector("[data-hero-prev]");
  const next   = document.querySelector("[data-hero-next]");
  if (!slides.length) return;

  let current  = 0;
  let timer    = null;

  function goTo(index) {
    slides[current].classList.remove("is-active");
    dots[current]?.classList.remove("is-active");
    current = (index + slides.length) % slides.length;
    slides[current].classList.add("is-active");
    dots[current]?.classList.add("is-active");
  }

  function autoplay() {
    clearInterval(timer);
    timer = setInterval(() => goTo(current + 1), 4500);
  }

  prev?.addEventListener("click", () => { goTo(current - 1); autoplay(); });
  next?.addEventListener("click", () => { goTo(current + 1); autoplay(); });
  dots.forEach((dot, i) => dot.addEventListener("click", () => { goTo(i); autoplay(); }));

  // Pause on hover
  document.querySelector(".hero-banner")?.addEventListener("mouseenter", () => clearInterval(timer));
  document.querySelector(".hero-banner")?.addEventListener("mouseleave", autoplay);

  autoplay();
}

/* ─── Featured Products (New Arrivals) ─── */
async function loadFeaturedProducts() {
  const grid = document.querySelector("[data-featured-grid]");
  if (!grid) return;

  grid.innerHTML = createSkeletonCards(4);
  startProgress();

  try {
    const data     = await get("/api/products?featured=true");
    const products = (Array.isArray(data) ? data : data.products || []).slice(0, 4);
    if (!products.length) { grid.innerHTML = ""; return; }
    grid.innerHTML = products.map(productCardMarkup).join("");
    bindProductCardActions(grid, products);
  } catch {
    grid.innerHTML = "";
  } finally {
    endProgress();
  }
}

/* ─── Trending Products (horizontal scroll) ─── */
async function loadTrendingProducts() {
  const wrap = document.querySelector("[data-trending-grid]");
  if (!wrap) return;

  wrap.innerHTML = createSkeletonCards(6);

  try {
    const data     = await get("/api/products");
    const products = (Array.isArray(data) ? data : data.products || []).slice(0, 8);
    if (!products.length) { wrap.closest(".trending-section")?.remove(); return; }
    wrap.innerHTML = products.map(productCardMarkup).join("");
    bindProductCardActions(wrap, products);
  } catch {
    wrap.closest(".trending-section")?.remove();
  }
}

/* ─── Customer Count Ticker ─── */
async function loadStats() {
  const el = document.getElementById("customerCount");
  if (!el) return;

  let target = 151;
  try {
    const data = await get("/api/stats");
    if (data?.customers) target = data.customers;
  } catch { /* use fallback */ }

  const start = performance.now();
  const duration = 1200;

  (function tick(now) {
    const p   = Math.min((now - start) / duration, 1);
    const val = Math.floor(p * (2 - p) * target);   // ease-out quad
    el.textContent = val;
    if (p < 1) requestAnimationFrame(tick);
    else el.textContent = target;
  })(start);
}

/* ─── Newsletter ─── */
function initNewsletter() {
  const form = document.querySelector("[data-newsletter-form]");
  if (!form) return;
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const input = form.querySelector("input[type=email]");
    const btn   = form.querySelector("button[type=submit]");
    const prev  = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-check"></i> Subscribed!';
    btn.disabled  = true;
    input.value   = "";
    setTimeout(() => { btn.innerHTML = prev; btn.disabled = false; }, 3000);
  });
}

/* ─── Boot ─── */
window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  initHeroSlider();
  initNewsletter();
  loadStats();
  loadFeaturedProducts();
  loadTrendingProducts();
});
