import { getWithFallback } from "../shared/api.js";
import { normalizeProduct } from "../shared/catalog.js";
import {
  bindProductCardActions,
  createEmptyMarkup,
  createSkeletonCards,
  initSite,
  productCardMarkup,
  startProgress,
  endProgress,
} from "../shared/site.js";

/* ───────────────────────────────────────────
   STATE
─────────────────────────────────────────── */
let allProducts  = [];
let activeFilters = {
  categories: [],   // string[]
  sizes:      [],   // string[]
  priceMin:   0,
  priceMax:   99999,
  inStockOnly: false,
};
let activeSortKey = "featured";
let viewMode      = "grid";

/* ───────────────────────────────────────────
   URL PARAMS → pre-select category
─────────────────────────────────────────── */
function readURLParams() {
  const params = new URLSearchParams(window.location.search);
  const cat = params.get("cat");
  if (cat) activeFilters.categories = [cat];
}

/* ───────────────────────────────────────────
   FILTER + SORT LOGIC
─────────────────────────────────────────── */
function applyFiltersAndSort() {
  let result = [...allProducts];

  // Category
  if (activeFilters.categories.length) {
    result = result.filter(p => {
      const cats = [
        ...(p.categories || []),
        ...(p.tags || []),
        p.category,
        p.type,
      ].filter(Boolean).map(c => c.toLowerCase());
      return activeFilters.categories.some(c => cats.some(pc => pc.includes(c)));
    });
  }

  // Size
  if (activeFilters.sizes.length) {
    result = result.filter(p => {
      const stock = p.stock || {};
      return activeFilters.sizes.some(s => (stock[s] ?? 1) > 0);
    });
  }

  // Price
  result = result.filter(p => {
    const price = p.price || p.selling_price || 0;
    return price >= activeFilters.priceMin && price <= activeFilters.priceMax;
  });

  // In-stock only
  if (activeFilters.inStockOnly) {
    result = result.filter(p => {
      const stock = p.stock || {};
      return Object.values(stock).some(v => v > 0) || p.in_stock !== false;
    });
  }

  // Sort
  result = sortProducts(result, activeSortKey);
  return result;
}

function sortProducts(list, key) {
  const arr = [...list];
  switch (key) {
    case "price-asc":  return arr.sort((a, b) => (a.price || 0) - (b.price || 0));
    case "price-desc": return arr.sort((a, b) => (b.price || 0) - (a.price || 0));
    case "name-asc":   return arr.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
    case "newest":     return arr.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    default:           return arr; // featured = API order
  }
}

/* ───────────────────────────────────────────
   RENDER PRODUCTS
─────────────────────────────────────────── */
function renderProducts() {
  const grid = document.querySelector("[data-products-grid]");
  if (!grid) return;

  const filtered = applyFiltersAndSort();

  // Update count
  const countEl = document.querySelector("[data-product-count]");
  if (countEl) countEl.textContent = filtered.length;

  // Render active filter chips
  renderActiveFilterChips();

  if (!filtered.length) {
    grid.innerHTML = createEmptyMarkup(
      "No products found",
      "Try adjusting your filters or clearing them to see all products.",
      "#",
      "Clear Filters",
    );
    grid.querySelector("a")?.addEventListener("click", (e) => {
      e.preventDefault();
      clearAllFilters();
    });
    return;
  }

  grid.innerHTML = filtered.map(productCardMarkup).join("");
  grid.setAttribute("data-view-mode", viewMode);
  bindProductCardActions(grid, filtered);
}

/* ───────────────────────────────────────────
   ACTIVE FILTER CHIPS
─────────────────────────────────────────── */
function renderActiveFilterChips() {
  const wrap = document.querySelector("[data-active-filters]");
  if (!wrap) return;

  const chips = [];

  activeFilters.categories.forEach(c => chips.push({ label: c, type: "cat", value: c }));
  activeFilters.sizes.forEach(s => chips.push({ label: `Size: ${s}`, type: "size", value: s }));
  if (activeFilters.priceMin > 0 || activeFilters.priceMax < 99999) {
    chips.push({ label: `₹${activeFilters.priceMin}–₹${activeFilters.priceMax}`, type: "price" });
  }
  if (activeFilters.inStockOnly) chips.push({ label: "In Stock Only", type: "stock" });

  wrap.hidden = chips.length === 0;
  wrap.innerHTML = chips.map(chip => `
    <span class="active-filter-chip">
      ${chip.label}
      <button type="button" data-remove-filter="${chip.type}" data-remove-value="${chip.value || ''}">
        <i class="fa-solid fa-xmark"></i>
      </button>
    </span>
  `).join("");

  wrap.querySelectorAll("[data-remove-filter]").forEach(btn => {
    btn.addEventListener("click", () => removeFilter(btn.dataset.removeFilter, btn.dataset.removeValue));
  });
}

function removeFilter(type, value) {
  switch (type) {
    case "cat":   activeFilters.categories = activeFilters.categories.filter(c => c !== value); break;
    case "size":  activeFilters.sizes = activeFilters.sizes.filter(s => s !== value); break;
    case "price": activeFilters.priceMin = 0; activeFilters.priceMax = 99999; break;
    case "stock": activeFilters.inStockOnly = false; break;
  }
  syncSidebarUI();
  renderProducts();
}

function clearAllFilters() {
  activeFilters = { categories: [], sizes: [], priceMin: 0, priceMax: 99999, inStockOnly: false };
  syncSidebarUI();
  renderProducts();
}

/* sync checkbox/range UI back to state */
function syncSidebarUI() {
  document.querySelectorAll("[data-filter-cat]").forEach(cb => {
    cb.checked = activeFilters.categories.includes(cb.value);
  });
  document.querySelectorAll("[data-filter-size]").forEach(cb => {
    cb.checked = activeFilters.sizes.includes(cb.value);
  });
  const inStock = document.querySelector("[data-filter-instock]");
  if (inStock) inStock.checked = activeFilters.inStockOnly;
  const minEl = document.querySelector("[data-price-min-label]");
  const maxEl = document.querySelector("[data-price-max-label]");
  if (minEl) minEl.textContent = activeFilters.priceMin;
  if (maxEl) maxEl.textContent = activeFilters.priceMax === 99999 ? "5000+" : activeFilters.priceMax;
}

/* ───────────────────────────────────────────
   SIDEBAR FILTER BINDINGS
─────────────────────────────────────────── */
function initFilters() {
  // Category checkboxes
  document.querySelectorAll("[data-filter-cat]").forEach(cb => {
    if (activeFilters.categories.includes(cb.value)) cb.checked = true;
    cb.addEventListener("change", () => {
      if (cb.checked) activeFilters.categories.push(cb.value);
      else activeFilters.categories = activeFilters.categories.filter(c => c !== cb.value);
      renderProducts();
    });
  });

  // Size chips
  document.querySelectorAll("[data-filter-size]").forEach(cb => {
    cb.addEventListener("change", () => {
      if (cb.checked) activeFilters.sizes.push(cb.value);
      else activeFilters.sizes = activeFilters.sizes.filter(s => s !== cb.value);
      renderProducts();
    });
  });

  // In-stock toggle
  const inStockCb = document.querySelector("[data-filter-instock]");
  inStockCb?.addEventListener("change", () => {
    activeFilters.inStockOnly = inStockCb.checked;
    renderProducts();
  });

  // Price range sliders
  const sliderMin = document.querySelector("[data-price-min]");
  const sliderMax = document.querySelector("[data-price-max]");
  const labelMin  = document.querySelector("[data-price-min-label]");
  const labelMax  = document.querySelector("[data-price-max-label]");

  function updatePriceUI() {
    let lo = parseInt(sliderMin?.value || 0);
    let hi = parseInt(sliderMax?.value || 5000);
    if (lo > hi) { [lo, hi] = [hi, lo]; }
    if (labelMin) labelMin.textContent = lo;
    if (labelMax) labelMax.textContent = hi >= 5000 ? "5000+" : hi;
    activeFilters.priceMin = lo;
    activeFilters.priceMax = hi >= 5000 ? 99999 : hi;
  }

  sliderMin?.addEventListener("input", () => { updatePriceUI(); renderProducts(); });
  sliderMax?.addEventListener("input", () => { updatePriceUI(); renderProducts(); });

  // Number inputs
  const inputMin = document.querySelector("[data-price-min-input]");
  const inputMax = document.querySelector("[data-price-max-input]");
  inputMin?.addEventListener("change", () => {
    activeFilters.priceMin = parseInt(inputMin.value) || 0;
    if (sliderMin) sliderMin.value = activeFilters.priceMin;
    if (labelMin)  labelMin.textContent = activeFilters.priceMin;
    renderProducts();
  });
  inputMax?.addEventListener("change", () => {
    const v = parseInt(inputMax.value) || 99999;
    activeFilters.priceMax = v >= 5000 ? 99999 : v;
    if (sliderMax) sliderMax.value = Math.min(v, 5000);
    if (labelMax)  labelMax.textContent = v >= 5000 ? "5000+" : v;
    renderProducts();
  });

  // Apply button (optional explicit apply)
  document.querySelector("[data-apply-filters]")?.addEventListener("click", renderProducts);

  // Clear all
  document.querySelector("[data-clear-filters]")?.addEventListener("click", clearAllFilters);

  // Accordion toggles
  document.querySelectorAll("[data-filter-accordion]").forEach(btn => {
    btn.addEventListener("click", () => {
      const body = btn.nextElementSibling;
      const open = body.classList.contains("is-open");
      body.classList.toggle("is-open", !open);
      btn.classList.toggle("is-collapsed", open);
    });
  });

  // Mobile filter toggle
  const toggleBtn = document.querySelector("[data-filter-toggle]");
  const sidebar   = document.querySelector("[data-filter-sidebar]");
  toggleBtn?.addEventListener("click", () => sidebar?.classList.toggle("is-open"));
  document.addEventListener("click", (e) => {
    if (sidebar?.classList.contains("is-open") && !sidebar.contains(e.target) && !toggleBtn?.contains(e.target)) {
      sidebar.classList.remove("is-open");
    }
  });
}

/* ───────────────────────────────────────────
   SORT + VIEW TOGGLE
─────────────────────────────────────────── */
function initControls() {
  // Sort select
  const sortSel = document.querySelector("[data-sort-select]");
  sortSel?.addEventListener("change", () => {
    activeSortKey = sortSel.value;
    renderProducts();
  });

  // Grid / List toggle
  document.querySelectorAll("[data-view]").forEach(btn => {
    btn.addEventListener("click", () => {
      viewMode = btn.dataset.view;
      document.querySelectorAll("[data-view]").forEach(b => b.classList.toggle("is-active", b === btn));
      const grid = document.querySelector("[data-products-grid]");
      if (grid) grid.setAttribute("data-view-mode", viewMode);
    });
  });
}

/* ───────────────────────────────────────────
   LOAD PRODUCTS
─────────────────────────────────────────── */
async function loadProducts() {
  const grid = document.querySelector("[data-products-grid]");
  if (!grid) return;

  grid.innerHTML = createSkeletonCards(12);
  startProgress();

  try {
    const data   = await getWithFallback(["/api/products"]);
    allProducts  = (Array.isArray(data) ? data : data.products || []).map(normalizeProduct);
    renderProducts();
  } catch (err) {
    grid.innerHTML = createEmptyMarkup("Failed to load products", err.message);
  } finally {
    endProgress();
  }
}

/* ───────────────────────────────────────────
   BOOT
─────────────────────────────────────────── */
window.addEventListener("DOMContentLoaded", async () => {
  readURLParams();
  await initSite();
  initFilters();
  initControls();
  loadProducts();
});
