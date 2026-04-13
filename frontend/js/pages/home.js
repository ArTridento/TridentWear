import { get } from "../shared/api.js";
import {
  bindProductCardActions,
  createSkeletonCards,
  initSite,
  productCardMarkup,
  startProgress,
  endProgress,
} from "../shared/site.js";

async function loadFeaturedProducts() {
  const grid = document.querySelector("[data-featured-grid]");
  if (!grid) return;

  grid.innerHTML = createSkeletonCards(4);
  startProgress();

  try {
    const data = await get("/api/products?featured=true");
    const products = (Array.isArray(data) ? data : data.products || []).slice(0, 4);
    grid.innerHTML = products.map(productCardMarkup).join("");
    bindProductCardActions(grid, products);
  } catch (error) {
    grid.innerHTML = `<div class="helper-note danger">${error.message}</div>`;
  } finally {
    endProgress();
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  await loadFeaturedProducts();
});
