import { get } from "../shared/api.js";
import { addCartItem } from "../shared/cart.js";
import { bindProductCardActions, createEmptyMarkup, createLoaderMarkup, formatCurrency, initSite, productCardMarkup, showToast } from "../shared/site.js";

let currentProduct = null;
let selectedSize = "";

function productIdFromQuery() {
  const params = new URLSearchParams(window.location.search);
  return Number(params.get("id"));
}

function bindSizeSelection(container) {
  container.querySelectorAll("[data-size-option]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedSize = button.dataset.sizeOption;
      container.querySelectorAll("[data-size-option]").forEach((chip) => chip.classList.remove("is-selected"));
      button.classList.add("is-selected");
    });
  });
}

function renderProduct(product) {
  const detail = document.querySelector("[data-product-detail]");
  selectedSize = product.sizes[0] || "M";

  detail.innerHTML = `
    <div class="detail-grid">
      <div class="detail-image-wrap">
        <img src="${product.image}" alt="${product.name}">
      </div>
      <div class="detail-panel">
        <span class="detail-category">${product.category === "shirt" ? "Tailored Shirt" : "Premium T-Shirt"}</span>
        <h1 class="detail-title">${product.name}</h1>
        <p class="detail-copy">${product.description}</p>
        <div class="detail-meta-row">
          <span class="pill">${product.tag || "Signature Drop"}</span>
          <span class="pill">${product.stock} in stock</span>
          <span class="pill">${product.featured ? "Featured" : "Core Collection"}</span>
        </div>
        <strong class="detail-price">${formatCurrency(product.price)}</strong>
        <div class="section-tight">
          <span class="label">Select size</span>
          <div class="detail-size-grid">
            ${product.sizes
              .map((size, index) => `<button class="size-chip ${index === 0 ? "is-selected" : ""}" type="button" data-size-option="${size}">${size}</button>`)
              .join("")}
          </div>
        </div>
        <div class="detail-actions">
          <button class="btn btn-primary" type="button" data-add-detail>Add to Cart</button>
          <a class="btn btn-outline" href="/cart">Go to Cart</a>
        </div>
      </div>
    </div>
  `;

  bindSizeSelection(detail);
  detail.querySelector("[data-add-detail]").addEventListener("click", () => {
    addCartItem(currentProduct, { size: selectedSize });
    showToast(`${currentProduct.name} (${selectedSize}) added to cart.`);
  });
}

async function renderRelatedProducts(product) {
  const grid = document.querySelector("[data-related-products]");
  const data = await get(`/api/products?category=${product.category}`);
  const related = data.products.filter((item) => item.id !== product.id).slice(0, 3);

  if (!related.length) {
    grid.innerHTML = createEmptyMarkup("No related drops yet", "Add more products to grow this collection.");
    return;
  }

  grid.innerHTML = related.map(productCardMarkup).join("");
  bindProductCardActions(grid, related);
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  const detail = document.querySelector("[data-product-detail]");
  const related = document.querySelector("[data-related-products]");
  detail.innerHTML = createLoaderMarkup("Loading product details...");
  related.innerHTML = createLoaderMarkup("Loading related pieces...");

  const id = productIdFromQuery();
  if (!id) {
    detail.innerHTML = createEmptyMarkup("Missing product", "Select a product from the collection first.");
    related.innerHTML = "";
    return;
  }

  try {
    const data = await get(`/api/products/${id}`);
    currentProduct = data.product;
    renderProduct(currentProduct);
    await renderRelatedProducts(currentProduct);
  } catch (error) {
    detail.innerHTML = createEmptyMarkup("Product unavailable", error.message);
    related.innerHTML = "";
  }
});
