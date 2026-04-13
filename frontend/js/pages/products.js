import { getWithFallback } from "../shared/api.js";
import { CATEGORY_GROUPS, getCategoryMeta, matchesCategory, normalizeProduct } from "../shared/catalog.js";
import {
  bindProductCardActions,
  createEmptyMarkup,
  createSkeletonCards,
  initSite,
  productCardMarkup,
  startProgress,
  endProgress,
} from "../shared/site.js";

let allProducts = [];
let activeFilter = "all";

function activeCategoryMeta() {
  return activeFilter === "all"
    ? {
        label: "All Categories",
        copy: "Browse all 18 T-shirt categories from the full TridentWear catalog.",
      }
    : getCategoryMeta(activeFilter);
}

function updateCategorySummary(filtered) {
  const count = document.querySelector("[data-product-count]");
  const activeLabel = document.querySelector("[data-active-category-label]");
  const activeCopy = document.querySelector("[data-active-category-copy]");
  const meta = activeCategoryMeta();

  count.textContent = `${filtered.length} product${filtered.length === 1 ? "" : "s"}`;
  activeLabel.textContent = meta?.label || "All Categories";
  activeCopy.textContent = meta?.copy || "Browse all T-shirt categories.";
}

function renderProducts() {
  const grid = document.querySelector("[data-products-grid]");
  const filtered = activeFilter === "all" ? allProducts : allProducts.filter((product) => matchesCategory(product, activeFilter));

  updateCategorySummary(filtered);

  if (!filtered.length) {
    grid.innerHTML = createEmptyMarkup(
      "No products in this category",
      "Pick another category or add more products from the admin page.",
      "/admin",
      "Open Admin",
    );
    return;
  }

  grid.innerHTML = filtered.map(productCardMarkup).join("");
  bindProductCardActions(grid, filtered);
}

function bindCategoryButtons() {
  document.querySelectorAll("[data-category-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      activeFilter = button.dataset.categoryFilter;
      document.querySelectorAll("[data-category-filter]").forEach((item) => {
        item.classList.toggle("is-active", item === button);
      });
      renderProducts();
    });
  });
}

function renderCategoryGroups() {
  const wrapper = document.querySelector("[data-category-groups]");
  wrapper.innerHTML = `
    <article class="category-group-card reveal">
      <button class="category-card is-active" type="button" data-category-filter="all">
        <span class="category-icon">18</span>
        <span class="category-name">All Categories</span>
        <span class="category-copy">View every T-shirt type in one grid.</span>
      </button>
    </article>
    ${CATEGORY_GROUPS.map((group, i) => `
      <section class="category-group-card reveal reveal-delay-${Math.min(i + 1, 4)}">
        <div class="category-group-head">
          <h2 class="category-group-title">${group.title}</h2>
          <p class="section-copy">Filter the catalog by ${group.title.toLowerCase()}.</p>
        </div>
        <div class="categories-grid">
          ${group.items.map((category) => `
            <button class="category-card" type="button" data-category-filter="${category.slug}">
              <span class="category-icon">${category.icon}</span>
              <span class="category-name">${category.label}</span>
              <span class="category-copy">${category.copy}</span>
            </button>
          `).join("")}
        </div>
      </section>
    `).join("")}
  `;

  bindCategoryButtons();
}

async function loadProducts() {
  const grid = document.querySelector("[data-products-grid]");
  grid.innerHTML = createSkeletonCards(6);
  startProgress();
  const data = await getWithFallback(["/api/products", "/products?format=json"]);
  allProducts = (Array.isArray(data) ? data : data.products || []).map(normalizeProduct);
  renderProducts();
  endProgress();
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  renderCategoryGroups();

  try {
    await loadProducts();
  } catch (error) {
    document.querySelector("[data-products-grid]").innerHTML = `<div class="helper-note danger">${error.message}</div>`;
    endProgress();
  }
});
