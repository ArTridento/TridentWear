import { getWithFallback } from "../shared/api.js?v=7";
import {
  bindProductCardActions,
  createEmptyMarkup,
  initSite,
  productCardMarkup,
  startProgress,
  endProgress,
} from "../shared/site.js?v=7";

/* ───────────────────────────────────────────
   STATE & CATEGORY MAP
─────────────────────────────────────────── */
let allProducts = [];
let activeCategory = "all";

const categoryLabels = {
  all:         "All Products",
  tshirt:      "T-Shirts",
  shirt:       "Shirts",
  kurta:       "Kurtas",
  hoodie:      "Hoodies",
  sweatshirt:  "Sweatshirts",
  jacket:      "Jackets",
  sweater:     "Sweaters",
  blazer:      "Blazers",
  tunic:       "Tunics",
};

/* ───────────────────────────────────────────
   READ ?cat= FROM URL
─────────────────────────────────────────── */
function getCatFromURL() {
  const params = new URLSearchParams(window.location.search);
  const cat = params.get("cat") || "all";
  return categoryLabels[cat] ? cat : "all";
}

/* ───────────────────────────────────────────
   FILTER PRODUCTS
─────────────────────────────────────────── */
function filterProducts(cat) {
  if (cat === "all") return allProducts;
  return allProducts.filter(p => p.category === cat);
}

/* ───────────────────────────────────────────
   RENDER PRODUCTS
─────────────────────────────────────────── */
function renderProducts(animate = true) {
  const grid = document.querySelector("[data-products-grid]");
  if (!grid) return;

  const filtered = filterProducts(activeCategory);

  // Update count
  const countEl = document.querySelector("[data-product-count]");
  if (countEl) countEl.textContent = filtered.length;

  if (!filtered.length) {
    grid.innerHTML = createEmptyMarkup(
      "No products found",
      "Try selecting a different category.",
      "products.html",
      "View All"
    );
    return;
  }

  if (animate) {
    grid.classList.add("fade-out");
    setTimeout(() => {
      grid.innerHTML = filtered.map(productCardMarkup).join("");
      bindProductCardActions(grid, filtered);
      grid.classList.remove("fade-out");
    }, 150);
  } else {
    grid.innerHTML = filtered.map(productCardMarkup).join("");
    bindProductCardActions(grid, filtered);
  }
}

/* ───────────────────────────────────────────
   UPDATE PAGE TITLE & BREADCRUMB
─────────────────────────────────────────── */
function updateLabels() {
  const label = categoryLabels[activeCategory] || "All Products";
  document.querySelectorAll("[data-active-category-label]").forEach(el => el.textContent = label);
  document.querySelectorAll("[data-active-category-label-h1]").forEach(el => el.textContent = label);
  document.title = `${label} | TridentWear`;
}

/* ───────────────────────────────────────────
   SYNC ACTIVE TAB
─────────────────────────────────────────── */
function syncTabs() {
  document.querySelectorAll("[data-main-category]").forEach(btn => {
    const isActive = btn.dataset.mainCategory === activeCategory;
    btn.classList.toggle("is-active", isActive);
  });

  // Scroll active tab into view
  const activeBtn = document.querySelector("[data-main-category].is-active");
  if (activeBtn) {
    activeBtn.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
  }
}

/* ───────────────────────────────────────────
   SWITCH CATEGORY
─────────────────────────────────────────── */
function switchCategory(cat) {
  if (cat === activeCategory) return;
  activeCategory = cat;

  // Update URL without reload
  const url = new URL(window.location.href);
  if (cat === "all") {
    url.searchParams.delete("cat");
  } else {
    url.searchParams.set("cat", cat);
  }
  window.history.replaceState({}, "", url.toString());

  syncTabs();
  updateLabels();
  renderProducts(true);

  // Scroll to grid
  setTimeout(() => {
    document.querySelector("[data-products-grid]")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 100);
}

/* ───────────────────────────────────────────
   INIT TABS
─────────────────────────────────────────── */
function initTabs() {
  document.querySelectorAll("[data-main-category]").forEach(btn => {
    btn.addEventListener("click", () => switchCategory(btn.dataset.mainCategory));
  });
}

/* ───────────────────────────────────────────
   LOAD & INIT
─────────────────────────────────────────── */
async function loadAndRender() {
  try {
    startProgress();
    allProducts = await getWithFallback(["/api/products"]);
    if (!Array.isArray(allProducts)) allProducts = allProducts.products || [];

    // Read cat from URL and set active
    activeCategory = getCatFromURL();
    syncTabs();
    updateLabels();
    renderProducts(false);
    initTabs();
  } catch (err) {
    console.error("Failed to load products:", err);
  } finally {
    endProgress();
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  await loadAndRender();
});
