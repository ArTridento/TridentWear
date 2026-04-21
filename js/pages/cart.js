import { resolveAssetUrl } from "../shared/api.js?v=9";
import { getCartSubtotal, loadCart, removeCartItem, updateCartItemQuantity } from "../shared/cart.js?v=9";
import { createEmptyMarkup, formatCurrency, initSite } from "../shared/site.js?v=9";

function renderSummary(items) {
  const summary = document.querySelector("[data-cart-summary]");
  if (!summary) return;
  const subtotal = getCartSubtotal(items);
  summary.innerHTML = `
    <div class="summary-row">
      <span>Subtotal</span>
      <strong class="summary-price">${formatCurrency(subtotal)}</strong>
    </div>
    <div class="summary-row">
      <span>Items</span>
      <strong>${items.length}</strong>
    </div>
  `;
}

function bindCartActions() {
  document.querySelectorAll("[data-qty-change]").forEach((button) => {
    button.addEventListener("click", () => {
      const { id, size, delta } = button.dataset;
      const item = loadCart().find((entry) => String(entry.id) === id && entry.size === size);
      if (!item) {
        return;
      }
      updateCartItemQuantity(Number(id), size, Number(item.qty) + Number(delta));
      renderCart();
    });
  });

  document.querySelectorAll("[data-remove-item]").forEach((button) => {
    button.addEventListener("click", () => {
      removeCartItem(Number(button.dataset.id), button.dataset.size);
      renderCart();
    });
  });
}

function renderCart() {
  const items = loadCart();
  const list = document.querySelector("[data-cart-list]");
  const checkoutBtn = document.querySelector("a[href='checkout.html']");

  if (!items.length) {
    if (list) list.innerHTML = createEmptyMarkup("Your cart is empty", "Add a few premium pieces and come back here.");
    if (checkoutBtn) checkoutBtn.style.pointerEvents = "none";
    if (checkoutBtn) checkoutBtn.classList.add("disabled");
    renderSummary(items);
    return;
  }

  if (checkoutBtn) checkoutBtn.style.pointerEvents = "auto";
  if (checkoutBtn) checkoutBtn.classList.remove("disabled");

  if (list) {
    list.innerHTML = items
      .map(
        (item) => `
          <article class="cart-item">
            <div class="cart-item-media">
              <img src="${resolveAssetUrl(item.image)}" alt="${item.name}">
            </div>
            <div>
              <div class="cart-item-title-row">
                <div>
                  <strong>${item.name}</strong>
                  <div class="label">Size ${item.size}</div>
                </div>
                <strong class="cart-item-price">${formatCurrency(item.price)}</strong>
              </div>
              <div class="cart-row-actions">
                <div class="quantity-control">
                  <button class="qty-button" type="button" data-qty-change data-id="${item.id}" data-size="${item.size}" data-delta="-1">-</button>
                  <span>${item.qty}</span>
                  <button class="qty-button" type="button" data-qty-change data-id="${item.id}" data-size="${item.size}" data-delta="1">+</button>
                </div>
                <button class="btn btn-outline" type="button" data-remove-item data-id="${item.id}" data-size="${item.size}">Remove</button>
              </div>
            </div>
          </article>
        `,
      )
      .join("");
  }

  renderSummary(items);
  bindCartActions();
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  const list = document.querySelector("[data-cart-list]");
  if (list) {
    list.innerHTML = `
      <div class="skeleton" style="height:8rem;margin-bottom:1rem;border-radius:var(--radius);"></div>
      <div class="skeleton" style="height:8rem;margin-bottom:1rem;border-radius:var(--radius);"></div>
      <div class="skeleton" style="height:8rem;margin-bottom:1rem;border-radius:var(--radius);"></div>
    `;
  }
  
  startGlobalLoader();
  setTimeout(() => {
    renderCart();
    endGlobalLoader();
    if (list) list.classList.add("fade-in");
  }, 500);
});
