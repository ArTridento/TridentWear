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
  const statNumbers = document.querySelectorAll("[data-count], [data-rating]");
  if (!statNumbers.length) return;

  // Get stats from API or use defaults
  let statsData = {
    customers: 15000,
    orders: 25000,
    rating: 4.8
  };

  try {
    const data = await get("/api/stats");
    if (data?.customers) statsData.customers = data.customers;
    if (data?.orders) statsData.orders = data.orders;
    if (data?.rating) statsData.rating = data.rating;
  } catch { /* use defaults */ }

  const animateNumber = (element, target, duration = 1800) => {
    const isRating = element.hasAttribute("data-rating");
    if (isRating) {
      // For rating, just set it directly since it's typically 4-5
      element.textContent = target;
      return;
    }

    const start = performance.now();
    const startVal = 0;

    const animate = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      
      // Ease-out cubic for smooth deceleration
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const currentVal = Math.floor(easeProgress * target);
      
      element.textContent = currentVal;
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        element.textContent = target;
      }
    };

    requestAnimationFrame(animate);
  };

  // Animate each stat
  statNumbers.forEach((el) => {
    if (el.hasAttribute("data-count")) {
      const target = parseInt(el.getAttribute("data-count"));
      animateNumber(el, target);
    } else if (el.hasAttribute("data-rating")) {
      animateNumber(el, parseFloat(el.getAttribute("data-rating")));
    }
  });
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
