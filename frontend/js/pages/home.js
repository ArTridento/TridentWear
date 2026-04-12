import { get } from "../shared/api.js";
import { bindProductCardActions, createLoaderMarkup, initSite, productCardMarkup } from "../shared/site.js";

async function loadFeaturedProducts() {
  const grid = document.querySelector("[data-featured-grid]");
  if (!grid) {
    return;
  }

  grid.innerHTML = createLoaderMarkup("Loading featured collection...");

  try {
    const data = await get("/api/products?featured=true");
    const products = data.products.slice(0, 4);
    grid.innerHTML = products.map(productCardMarkup).join("");
    bindProductCardActions(grid, products);
  } catch (error) {
    grid.innerHTML = `<div class="helper-note danger">${error.message}</div>`;
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  await loadFeaturedProducts();
});
