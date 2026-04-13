import { postWithFallback } from "../shared/api.js";
import { clearCart, getCartSubtotal, loadCart } from "../shared/cart.js";
import { formatCurrency, getCurrentUser, initSite, showToast } from "../shared/site.js";

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
    <div class="summary-row">
      <span>Shipping</span>
      <strong>Calculated locally</strong>
    </div>
  `;
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
  if (!form) return;
  
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
      
      const whatsappText = encodeURIComponent(`Hello TridentWear! I placed an order ${data.order_id}.`);
      const whatsappLink = `https://wa.me/919876543210?text=${whatsappText}`;
      
      clearCart();
      form.reset();
      showToast(`Order placed. ID: ${data.order_id}`);
      document.querySelector("[data-order-status]").innerHTML = `
        <div class="helper-note success" style="display: flex; flex-direction: column; gap: 0.5rem;">
          <strong>${data.order_id}</strong>
          <span>Your order has been saved successfully!</span>
          <a class="btn btn-secondary" href="${whatsappLink}" target="_blank">Order via WhatsApp</a>
        </div>
      `;
      // Optionally hide the form after success
      form.style.display = 'none';
      const summary = document.querySelector("[data-cart-summary]");
      if(summary) summary.innerHTML = "";
      
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      button.disabled = false;
      button.textContent = "Place Order";
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  const items = loadCart();
  renderSummary(items);
  prefillUser();
  bindCheckout();
});
