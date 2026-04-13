import { get, post } from "../shared/api.js";
import { formatCurrency, getCurrentUser, initSite, showToast } from "../shared/site.js";
import { resolveAssetUrl } from "../shared/api.js";

async function loadWishlist() {
  const container = document.querySelector("[data-wishlist-grid]");
  const empty = document.querySelector("[data-wishlist-empty]");

  try {
    const items = await get("/api/wishlist");
    if (!items || !items.length) {
      container.innerHTML = "";
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    container.innerHTML = items.map(({ product }) => `
      <article class="product-card reveal">
        <a class="product-media" href="/product?id=${product.id}">
          <img src="${resolveAssetUrl(product.image)}" alt="${product.name}" loading="lazy">
        </a>
        <div class="product-body">
          <div class="product-topline">
            <span class="product-label">${product.category}</span>
            ${product.tag ? `<span class="product-tag">${product.tag}</span>` : ""}
          </div>
          <h3 class="product-name">${product.name}</h3>
          <div class="product-footer">
            <strong class="product-price">${formatCurrency(product.price)}</strong>
            <div class="cart-row-actions">
              <a class="btn btn-outline" href="/product?id=${product.id}">View</a>
              <button class="btn btn-outline" type="button" data-remove-wish="${product.id}" style="color:var(--danger);border-color:var(--danger);">
                ♥ Remove
              </button>
            </div>
          </div>
        </div>
      </article>
    `).join("");

    container.querySelectorAll("[data-remove-wish]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = Number(btn.dataset.removeWish);
        try {
          await post("/api/wishlist/remove", { product_id: id }, "DELETE");
          showToast("Removed from wishlist.");
          await loadWishlist();
        } catch (err) {
          showToast(err.message, "error");
        }
      });
    });

  } catch (err) {
    container.innerHTML = `<div class="helper-note danger">${err.message}</div>`;
  }
}

// Custom DELETE helper since api.js doesn't export one for payload
async function removeFromWishlist(productId) {
  const { request } = await import("../shared/api.js");
  return request("/api/wishlist/remove", {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId }),
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  const user = getCurrentUser();
  if (!user) {
    window.location.href = "/login?next=" + encodeURIComponent("/wishlist");
    return;
  }

  // Re-bind remove buttons with correct method
  const container = document.querySelector("[data-wishlist-grid]");
  try {
    const items = await get("/api/wishlist");
    const empty = document.querySelector("[data-wishlist-empty]");
    if (!items || !items.length) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    container.innerHTML = items.map(({ product }) => `
      <article class="product-card reveal">
        <a class="product-media" href="/product?id=${product.id}">
          <img src="${resolveAssetUrl(product.image)}" alt="${product.name}" loading="lazy">
        </a>
        <div class="product-body">
          <div class="product-topline">
            <span class="product-label">${product.category}</span>
            ${product.tag ? `<span class="product-tag">${product.tag}</span>` : ""}
          </div>
          <h3 class="product-name">${product.name}</h3>
          <p class="product-description">${product.description}</p>
          <div class="product-footer">
            <strong class="product-price">${formatCurrency(product.price)}</strong>
            <div class="cart-row-actions">
              <a class="btn btn-outline" href="/product?id=${product.id}">View</a>
              <button class="btn btn-outline" type="button" data-remove-wish="${product.id}" style="color:var(--danger);border-color:var(--danger);">Remove ♥</button>
            </div>
          </div>
        </div>
      </article>
    `).join("");

    container.querySelectorAll("[data-remove-wish]").forEach(btn => {
      btn.addEventListener("click", async () => {
        try {
          await removeFromWishlist(Number(btn.dataset.removeWish));
          showToast("Removed from wishlist.");
          btn.closest("article").remove();
          if (!container.querySelectorAll("article").length) {
            document.querySelector("[data-wishlist-empty]").hidden = false;
          }
        } catch (err) {
          showToast(err.message, "error");
        }
      });
    });
  } catch (err) {
    container.innerHTML = `<div class="helper-note danger">${err.message}</div>`;
  }
});
