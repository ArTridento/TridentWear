import { get, post } from "./api.js";
import { addCartItem, getCartCount, loadCart, syncCart } from "./cart.js";

let currentUser = null;

export function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function toastStack() {
  let stack = document.querySelector("[data-toast-stack]");
  if (!stack) {
    stack = document.createElement("div");
    stack.className = "toast-stack";
    stack.setAttribute("data-toast-stack", "");
    document.body.appendChild(stack);
  }
  return stack;
}

export function showToast(message, type = "success") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;
  toastStack().appendChild(toast);
  window.setTimeout(() => toast.remove(), 2800);
}

export function createLoaderMarkup(label = "Loading...") {
  return `
    <div class="loader-state">
      <strong>${escapeHtml(label)}</strong>
      <span class="empty-copy">Pulling the latest from the Trident store.</span>
    </div>
  `;
}

export function createEmptyMarkup(title, copy, href = "/products", label = "Browse Products") {
  return `
    <div class="empty-state">
      <strong class="section-title">${escapeHtml(title)}</strong>
      <span class="empty-copy">${escapeHtml(copy)}</span>
      <a class="btn btn-secondary" href="${href}">${escapeHtml(label)}</a>
    </div>
  `;
}

export function productCardMarkup(product) {
  return `
    <article class="product-card">
      <a class="product-media" href="/product?id=${product.id}">
        <img src="${escapeHtml(product.image)}" alt="${escapeHtml(product.name)}">
      </a>
      <div class="product-body">
        <div class="product-topline">
          <span class="product-label">${product.category === "shirt" ? "Shirt" : "T-Shirt"}</span>
          ${product.tag ? `<span class="pill product-tag">${escapeHtml(product.tag)}</span>` : ""}
        </div>
        <h3 class="product-name">${escapeHtml(product.name)}</h3>
        <p class="product-description">${escapeHtml(product.description)}</p>
        <div class="detail-meta-row">
          ${product.sizes.map((size) => `<span class="pill">${escapeHtml(size)}</span>`).join("")}
        </div>
        <div class="product-footer">
          <strong class="product-price">${formatCurrency(product.price)}</strong>
          <div class="cart-row-actions">
            <a class="btn btn-outline" href="/product?id=${product.id}">View</a>
            <button class="btn btn-primary" type="button" data-add-to-cart data-product-id="${product.id}">Add to Cart</button>
          </div>
        </div>
      </div>
    </article>
  `;
}

export function bindProductCardActions(container, products) {
  const lookup = new Map(products.map((product) => [String(product.id), product]));

  container.querySelectorAll("[data-add-to-cart]").forEach((button) => {
    button.addEventListener("click", () => {
      const product = lookup.get(button.dataset.productId);
      if (!product) {
        return;
      }

      addCartItem(product);
      showToast(`${product.name} added to cart.`);
      button.textContent = "Added";
      window.setTimeout(() => {
        button.textContent = "Add to Cart";
      }, 1200);
    });
  });
}

function setActiveNav() {
  const currentPage = document.body.dataset.page;
  document.querySelectorAll("[data-nav-link]").forEach((link) => {
    link.classList.toggle("is-active", link.dataset.navLink === currentPage);
  });
}

function setCartCount(count) {
  document.querySelectorAll("[data-cart-count]").forEach((badge) => {
    badge.textContent = String(count);
  });
}

function setAccountUi() {
  const accountLink = document.querySelector("[data-account-link]");
  const logoutButton = document.querySelector("[data-logout-button]");
  const adminLink = document.querySelector("[data-admin-link]");

  if (accountLink) {
    if (!currentUser) {
      accountLink.textContent = "Login";
      accountLink.setAttribute("href", "/auth");
    } else if (currentUser.role === "admin") {
      accountLink.textContent = "Admin";
      accountLink.setAttribute("href", "/admin");
    } else {
      accountLink.textContent = currentUser.name.split(" ")[0];
      accountLink.setAttribute("href", "/auth");
    }
  }

  if (logoutButton) {
    logoutButton.hidden = !currentUser;
  }

  if (adminLink) {
    adminLink.hidden = !(currentUser && currentUser.role === "admin");
  }
}

function bindMobileMenu() {
  const toggle = document.querySelector("[data-mobile-toggle]");
  const nav = document.querySelector("[data-mobile-nav]");
  if (!toggle || !nav) {
    return;
  }

  toggle.addEventListener("click", () => {
    nav.classList.toggle("is-open");
  });

  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => nav.classList.remove("is-open"));
  });
}

function bindLogout() {
  const button = document.querySelector("[data-logout-button]");
  if (!button) {
    return;
  }

  button.addEventListener("click", async () => {
    try {
      await post("/api/auth/logout", {});
      currentUser = null;
      setAccountUi();
      showToast("Signed out successfully.");
      if (document.body.dataset.page === "admin") {
        window.location.href = "/auth";
      }
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

export async function refreshAuthState() {
  try {
    const data = await get("/api/auth/me");
    currentUser = data.user;
  } catch {
    currentUser = null;
  }
  setAccountUi();
  return currentUser;
}

export function getCurrentUser() {
  return currentUser;
}

export async function initSite() {
  setActiveNav();
  bindMobileMenu();
  bindLogout();
  setCartCount(getCartCount(loadCart()));
  window.addEventListener("trident:cart-change", (event) => {
    setCartCount(event.detail.count);
  });
  syncCart();
  await refreshAuthState();
}
