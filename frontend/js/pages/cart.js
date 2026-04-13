import { postWithFallback, resolveAssetUrl } from "../shared/api.js";
import { clearCart, getCartSubtotal, loadCart, removeCartItem, updateCartItemQuantity } from "../shared/cart.js";
import { createEmptyMarkup, formatCurrency, getCurrentUser, initSite, showToast } from "../shared/site.js";

function renderSummary(items) {
  const summary = document.querySelector("[data-cart-summary]");
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
    <div class="summary-row">
      <span>Shipping</span>
      <strong>Calculated locally</strong>
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
  const button = document.querySelector("[data-checkout-button]");

  if (!items.length) {
    list.innerHTML = createEmptyMarkup("Your cart is empty", "Add a few premium pieces and come back here.");
    button.disabled = true;
    renderSummary(items);
    return;
  }

  button.disabled = false;
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

  renderSummary(items);
  bindCartActions();
}

function prefillUser() {
  const user = getCurrentUser();
  if (!user) {
    return;
  }

  const nameField = document.querySelector("#checkout-name");
  const emailField = document.querySelector("#checkout-email");
  if (nameField && !nameField.value) {
    nameField.value = user.name;
  }
  if (emailField && !emailField.value) {
    emailField.value = user.email;
  }
}

function bindCheckout() {
  const form = document.querySelector("[data-checkout-form]");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const items = loadCart();
    if (!items.length) {
      showToast("Your cart is empty.", "error");
      return;
    }

    const payload = {
      items,
      subtotal: getCartSubtotal(items),
      customer: {
        name: form.querySelector("#checkout-name").value.trim(),
        email: form.querySelector("#checkout-email").value.trim(),
        phone: form.querySelector("#checkout-phone").value.trim(),
      },
      shipping: {
        address: form.querySelector("#checkout-address").value.trim(),
        city: form.querySelector("#checkout-city").value.trim(),
        postal_code: form.querySelector("#checkout-postal").value.trim(),
        country: form.querySelector("#checkout-country").value.trim(),
        notes: form.querySelector("#checkout-notes").value.trim(),
      },
    };

    const button = document.querySelector("[data-checkout-button]");
    button.disabled = true;
    button.textContent = "Placing Order...";

    try {
      const data = await postWithFallback(["/api/orders", "/orders"], payload);
      clearCart();
      renderCart();
      form.reset();
      showToast(`Order placed. ID: ${data.order_id}`);
      document.querySelector("[data-order-status]").innerHTML = `
        <div class="helper-note success">
          <strong>${data.order_id}</strong>
          <span>Your order has been saved locally and is ready for fulfilment.</span>
        </div>
      `;
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = "Place Order";
      prefillUser();
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  prefillUser();
  renderCart();
  bindCheckout();
});
