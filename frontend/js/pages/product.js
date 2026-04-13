import { getWithFallback, resolveAssetUrl } from "../shared/api.js";
import { addCartItem } from "../shared/cart.js";
import { SIZE_CHART, normalizeProduct, relatedProducts } from "../shared/catalog.js";
import { bindProductCardActions, createEmptyMarkup, createLoaderMarkup, formatCurrency, initSite, productCardMarkup, showToast } from "../shared/site.js";

let currentProduct = null;
let selectedSize = "";

function productIdFromQuery() {
  const params = new URLSearchParams(window.location.search);
  return Number(params.get("id"));
}

function modalRoot() {
  let modal = document.querySelector("[data-size-chart-modal]");
  if (!modal) {
    modal = document.createElement("div");
    modal.className = "modal-shell";
    modal.setAttribute("data-size-chart-modal", "");
    modal.hidden = true;
    modal.innerHTML = `
      <div class="modal-backdrop" data-close-size-chart></div>
      <div class="modal-card" role="dialog" aria-modal="true" aria-labelledby="size-chart-title">
        <div class="modal-head">
          <div>
            <span class="eyebrow">Size Chart</span>
            <h2 class="section-title" id="size-chart-title">TridentWear T-Shirt Fit Guide</h2>
          </div>
          <button class="btn btn-outline" type="button" data-close-size-chart>Close</button>
        </div>
        <div class="table-wrap">
          <table class="size-chart-table">
            <thead>
              <tr>
                <th>Size</th>
                <th>Chest (inches)</th>
                <th>Length (inches)</th>
              </tr>
            </thead>
            <tbody>
              ${SIZE_CHART.map((row) => `
                <tr>
                  <td>${row.size}</td>
                  <td>${row.chest}</td>
                  <td>${row.length}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    modal.querySelectorAll("[data-close-size-chart]").forEach((button) => {
      button.addEventListener("click", () => {
        modal.hidden = true;
        document.body.classList.remove("modal-open");
      });
    });
  }
  return modal;
}

function openSizeChart() {
  const modal = modalRoot();
  modal.hidden = false;
  document.body.classList.add("modal-open");
}

function clearSizeError(container) {
  const error = container.querySelector("[data-size-error]");
  if (error) {
    error.hidden = true;
  }
}

function bindSizeSelection(container) {
  container.querySelectorAll("[data-size-option]").forEach((button) => {
    button.addEventListener("click", () => {
      selectedSize = button.dataset.sizeOption;
      container.querySelectorAll("[data-size-option]").forEach((chip) => chip.classList.remove("is-selected"));
      button.classList.add("is-selected");
      clearSizeError(container);
    });
  });
}

function renderProduct(product) {
  const item = normalizeProduct(product);
  const detail = document.querySelector("[data-product-detail]");
  selectedSize = "";

  detail.innerHTML = `
    <div class="detail-grid">
      <div class="detail-image-wrap">
        <img src="${resolveAssetUrl(item.image)}" alt="${item.name}">
      </div>
      <div class="detail-panel">
        <span class="detail-category">Product Detail</span>
        <h1 class="detail-title">${item.name}</h1>
        <div class="detail-meta-row">
          ${item.card_tags.map((tag) => `<span class="pill">${tag}</span>`).join("")}
          <span class="pill">${item.stock} in stock</span>
        </div>
        <strong class="detail-price">${formatCurrency(item.price)}</strong>
        <p class="detail-copy">${item.description}</p>
        <div class="spec-grid">
          <article class="spec-card">
            <span class="label">Material</span>
            <strong>${item.material}</strong>
          </article>
          <article class="spec-card">
            <span class="label">GSM</span>
            <strong>${item.gsm} GSM</strong>
          </article>
          <article class="spec-card">
            <span class="label">Fit Type</span>
            <strong>${item.fit_type}</strong>
          </article>
          <article class="spec-card">
            <span class="label">Neck Type</span>
            <strong>${item.neck_type}</strong>
          </article>
        </div>
        <div class="product-category-list">
          ${item.category_labels.map((label) => `<span class="pill">${label}</span>`).join("")}
        </div>
        <div class="detail-size-panel">
          <div class="detail-meta-row">
            <span class="label">Select Size</span>
            <button class="btn btn-outline" type="button" data-view-size-chart>View Size Chart</button>
          </div>
          <div class="detail-size-grid">
            ${item.sizes.map((size) => `<button class="size-chip" type="button" data-size-option="${size}">${size}</button>`).join("")}
          </div>
          <div class="helper-note danger" data-size-error hidden>Please select a size before adding to cart.</div>
        </div>
        <div class="detail-actions">
          <button class="btn btn-primary" type="button" data-add-detail>Add to Cart</button>
          <a class="btn btn-outline" href="/cart">Go to Cart</a>
        </div>
      </div>
    </div>
  `;

  detail.querySelector("[data-view-size-chart]").addEventListener("click", openSizeChart);
  bindSizeSelection(detail);
  detail.querySelector("[data-add-detail]").addEventListener("click", () => {
    if (!selectedSize) {
      detail.querySelector("[data-size-error]").hidden = false;
      return;
    }

    addCartItem(item, { size: selectedSize });
    showToast(`${item.name} (${selectedSize}) added to cart.`);
  });
}

async function renderRelated(product) {
  const grid = document.querySelector("[data-related-products]");
  const data = await getWithFallback(["/api/products", "/products?format=json"]);
  const products = (Array.isArray(data) ? data : data.products || []).map(normalizeProduct);
  const related = relatedProducts(products, product).slice(0, 4);

  if (!related.length) {
    grid.innerHTML = createEmptyMarkup("No related styles yet", "Add more T-shirts to expand this category mix.");
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
  related.innerHTML = createLoaderMarkup("Loading related products...");

  const id = productIdFromQuery();
  if (!id) {
    detail.innerHTML = createEmptyMarkup("Missing product", "Select a product from the collection first.");
    related.innerHTML = "";
    return;
  }

  try {
    const data = await getWithFallback([`/api/products/${id}`, `/products/${id}`]);
    currentProduct = normalizeProduct(data.product || data);
    renderProduct(currentProduct);
    await renderRelated(currentProduct);
  } catch (error) {
    detail.innerHTML = createEmptyMarkup("Product unavailable", error.message);
    related.innerHTML = "";
  }
});
