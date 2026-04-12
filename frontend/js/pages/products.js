import { get } from "../shared/api.js";
import { bindProductCardActions, createEmptyMarkup, createLoaderMarkup, initSite, productCardMarkup } from "../shared/site.js";

let allProducts = [];

function renderProducts(filter = "all") {
  const grid = document.querySelector("[data-products-grid]");
  const count = document.querySelector("[data-product-count]");

  const filtered = filter === "all" ? allProducts : allProducts.filter((product) => product.category === filter);
  count.textContent = `${filtered.length} piece${filtered.length === 1 ? "" : "s"}`;

  if (!filtered.length) {
    grid.innerHTML = createEmptyMarkup(
      "Nothing in this lane yet",
      "Switch filters or add more products from the admin panel.",
      "/admin",
      "Open Admin",
    );
    return;
  }

  grid.innerHTML = filtered.map(productCardMarkup).join("");
  bindProductCardActions(grid, filtered);
}

async function loadProducts() {
  const grid = document.querySelector("[data-products-grid]");
  grid.innerHTML = createLoaderMarkup("Loading collection...");
  const data = await get("/api/products");
  allProducts = data.products;
  renderProducts("all");
}

function bindFilters() {
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-filter]").forEach((chip) => chip.classList.remove("is-active"));
      button.classList.add("is-active");
      renderProducts(button.dataset.filter);
    });
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  bindFilters();

  try {
    await loadProducts();
  } catch (error) {
    document.querySelector("[data-products-grid]").innerHTML = `<div class="helper-note danger">${error.message}</div>`;
  }
});
