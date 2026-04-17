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
   STATE & CATEGORY MAPPING
─────────────────────────────────────────── */
let allProducts = [];
let activeCategory = "all"; // Currently selected category
const categoryLabels = {
  all: "All T-Shirts",
  "crew-neck": "Crew Neck T-Shirts",
  polo: "Polo T-Shirts",
  "v-neck": "V-Neck T-Shirts",
  henley: "Henley T-Shirts",
  graphic: "Graphic T-Shirts",
  plain: "Plain T-Shirts",
  printed: "Printed T-Shirts",
  typography: "Typography T-Shirts",
  striped: "Striped T-Shirts",
  "color-block": "Color Block T-Shirts",
  washed: "Washed T-Shirts",
  "tie-dye": "Tie-Dye T-Shirts",
  "full-sleeve": "Full Sleeve T-Shirts",
  "half-sleeve": "Half Sleeve T-Shirts",
  "slim-fit": "Slim Fit T-Shirts",
  "regular-fit": "Regular Fit T-Shirts",
  "oversized-fit": "Oversized T-Shirts",
  "gym-wear": "Gym Wear T-Shirts",
  streetwear: "Streetwear T-Shirts",
  "new-arrivals": "New Arrivals",
};

/* ───────────────────────────────────────────
   FILTER PRODUCTS BY CATEGORY
─────────────────────────────────────────── */
function filterByCategory(categorySlug) {
  if (categorySlug === "all") {
    return allProducts.filter(p => p.category === "tshirt");
  }
  return allProducts.filter(p => p.category === "tshirt" && p.subcategory === categorySlug);
}

/* ───────────────────────────────────────────
   RENDER PRODUCTS WITH ANIMATION
─────────────────────────────────────────── */
function renderProducts(animate = true) {
  const grid = document.querySelector("[data-products-grid]");
  if (!grid) return;

  const filtered = filterByCategory(activeCategory);
  const countEl = document.querySelector("[data-product-count]");
  if (countEl) countEl.textContent = filtered.length;

  if (!filtered.length) {
    grid.innerHTML = createEmptyMarkup(
      "No products found",
      "Try selecting a different category.",
      "#",
      "View All",
    );
    return;
  }

  // Add fade-out animation
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
   UPDATE CATEGORY LABEL & BREADCRUMB
─────────────────────────────────────────── */
function updateCategoryLabels() {
  const label = categoryLabels[activeCategory] || "All T-Shirts";
  
  document.querySelectorAll("[data-active-category-label]").forEach(el => {
    el.textContent = label;
  });
  
  document.querySelectorAll("[data-active-category-label-h1]").forEach(el => {
    el.textContent = label;
  });
}

/* ───────────────────────────────────────────
   CATEGORY TAB CLICK HANDLER
─────────────────────────────────────────── */
function handleCategoryClick(button) {
  const categorySlug = button.dataset.category;
  if (categorySlug === activeCategory) return; // Already selected

  // Remove active class from all tabs
  document.querySelectorAll("[data-category]").forEach(tab => {
    tab.classList.remove("is-active");
  });

  // Add active class to clicked tab
  button.classList.add("is-active");

  // Update active category
  activeCategory = categorySlug;

  // Update breadcrumb and title
  updateCategoryLabels();

  // Re-render products with animation
  renderProducts(true);

  // Scroll to top of products
  setTimeout(() => {
    document.querySelector("[data-products-grid]")?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, 100);
}

/* ───────────────────────────────────────────
   INIT CATEGORY TABS
─────────────────────────────────────────── */
function initCategoryTabs() {
  document.querySelectorAll("[data-category]").forEach(button => {
    button.addEventListener("click", () => handleCategoryClick(button));
  });

  // Horizontal scroll container
  const scrollContainer = document.querySelector("[data-category-scroll]");
  if (scrollContainer) {
    // Scroll buttons (optional for mobile)
    // You can add prev/next buttons if needed
  }
}

/* ───────────────────────────────────────────
   LOAD DATA & INIT PAGE
─────────────────────────────────────────── */
async function loadAndRender() {
  try {
    startProgress();
    allProducts = await getWithFallback(["/api/products", "products.html?format=json"]);
    if (!Array.isArray(allProducts)) allProducts = allProducts.products || [];
    
    if (allProducts.length) {
      renderProducts(false); // Initial render without animation
      initCategoryTabs();
    }
  } catch (err) {
    console.error("Failed to load products:", err);
  } finally {
    endProgress();
  }
}

/* ───────────────────────────────────────────
   PAGE INIT
─────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  await loadAndRender();
});
