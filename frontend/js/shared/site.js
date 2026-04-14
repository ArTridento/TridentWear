import { clearAuthSession, get, getAuthSession, post, resolveAssetUrl, saveAuthSession } from "./api.js";
import { addCartItem, getCartCount, loadCart, syncCart } from "./cart.js";
import { normalizeProduct } from "./catalog.js";

let currentUser = null;

/* ───────── Currency ───────── */

export function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

/* ───────── HTML escaping ───────── */

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

/* ───────── Toast system ───────── */

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
  const bar = document.createElement("div");
  bar.className = "toast-progress";
  toast.appendChild(bar);
  toastStack().appendChild(toast);
  window.setTimeout(() => {
    toast.classList.add("removing");
    window.setTimeout(() => toast.remove(), 300);
  }, 2800);
}

/* ───────── Skeleton loaders ───────── */

export function createSkeletonCards(count = 3) {
  return Array.from({ length: count }, () => `
    <div class="skeleton-card">
      <div class="skeleton skeleton-media"></div>
      <div class="skeleton-body">
        <div class="skeleton skeleton-line short"></div>
        <div class="skeleton skeleton-line long"></div>
        <div class="skeleton skeleton-line medium"></div>
        <div class="skeleton skeleton-line price"></div>
      </div>
    </div>
  `).join("");
}

export function createLoaderMarkup(label = "Loading...") {
  return `<div class="loader-state"><strong>${escapeHtml(label)}</strong></div>`;
}

export function createEmptyMarkup(title, copy, href = "products.html", label = "Browse Products") {
  return `
    <div class="empty-state">
      <strong class="section-title">${escapeHtml(title)}</strong>
      <span class="empty-copy">${escapeHtml(copy)}</span>
      <a class="btn btn-secondary" href="${href}">${escapeHtml(label)}</a>
    </div>
  `;
}

/* ───────── Product card markup ───────── */

export function productCardMarkup(product) {
  const item = normalizeProduct(product);
  const productImage = resolveAssetUrl(item.image);
  const cardTags = item.card_tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join('<span class="tag-separator">&#8226;</span>');
  const wishlisted = isWishlisted(item.id);

  return `
    <article class="product-card reveal">
      <a class="product-media" href="product.html?id=${item.id}">
        <img src="${escapeHtml(productImage)}" alt="${escapeHtml(item.name)}" loading="lazy">
        <div class="product-media-overlay">
          <button class="btn btn-primary" type="button" data-quick-view data-product-id="${item.id}">Quick View</button>
        </div>
        <button class="wishlist-btn${wishlisted ? " is-wishlisted" : ""}" type="button" data-wishlist-toggle data-product-id="${item.id}" aria-label="Toggle wishlist">
          <svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
        </button>
      </a>
      <div class="product-body">
        <div class="product-topline">
          <span class="product-label">T-Shirt</span>
          ${item.tag ? `<span class="pill product-tag">${escapeHtml(item.tag)}</span>` : ""}
        </div>
        <h3 class="product-name">${escapeHtml(item.name)}</h3>
        <p class="product-description">${escapeHtml(item.description)}</p>
        <div class="product-card-tags">${cardTags}</div>
        <div class="product-category-list">
          ${item.category_labels.slice(0, 3).map((label) => `<span class="pill">${escapeHtml(label)}</span>`).join("")}
        </div>
        <div class="product-footer">
          <strong class="product-price">${formatCurrency(item.price)}</strong>
          <div class="cart-row-actions">
            <a class="btn btn-outline" href="product.html?id=${item.id}">View</a>
            <button class="btn btn-primary" type="button" data-add-to-cart data-product-id="${item.id}">Add to Cart</button>
          </div>
        </div>
      </div>
    </article>
  `;
}

/* ───────── Bind product card actions ───────── */

export function bindProductCardActions(container, products) {
  const lookup = new Map(products.map((product) => {
    const item = normalizeProduct(product);
    return [String(item.id), item];
  }));

  container.querySelectorAll("[data-add-to-cart]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const product = lookup.get(button.dataset.productId);
      if (!product) return;
      const defaultSize = product.sizes?.[0] || "M";
      try {
        addCartItem(product, { size: defaultSize });
        showToast(`${product.name} (${defaultSize}) added to cart.`);
        button.textContent = "Added ✓";
        window.setTimeout(() => { button.textContent = "Add to Cart"; }, 1200);
      } catch (err) {
        showToast(err.message, "error");
      }
    });
  });

  container.querySelectorAll("[data-wishlist-toggle]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const productId = Number(button.dataset.productId);
      const product = lookup.get(String(productId));
      toggleWishlist(productId);
      button.classList.toggle("is-wishlisted");
      button.classList.add("wishlist-pop");
      window.setTimeout(() => button.classList.remove("wishlist-pop"), 400);
      if (button.classList.contains("is-wishlisted")) {
        showToast(`${product?.name || "Item"} added to wishlist.`);
      }
    });
  });

  container.querySelectorAll("[data-quick-view]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      const product = lookup.get(button.dataset.productId);
      if (product) openQuickView(product);
    });
  });

  observeReveals(container);
}

/* ───────── Wishlist (localStorage) ───────── */

export const localWishlist = new Set();

export function isWishlisted(id) {
  return localWishlist.has(Number(id));
}

export async function toggleWishlist(id) {
  const numId = Number(id);
  const user = getCurrentUser();
  if (!user) {
    showToast("Please login to use wishlist.", "error");
    window.location.href = "login.html?next=/wishlist";
    throw new Error("unauthorized");
  }

  if (localWishlist.has(numId)) {
    localWishlist.delete(numId);
    let { request } = await import("./api.js");
    await request("/api/wishlist/remove", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: numId }),
    }).catch(() => null);
  } else {
    localWishlist.add(numId);
    await post("/api/wishlist/add", { product_id: numId }).catch(() => null);
  }
}

/* ───────── Quick View Modal ───────── */

function openQuickView(product) {
  let modal = document.querySelector("[data-quick-view-modal]");
  if (modal) modal.remove();

  const item = normalizeProduct(product);
  const productImage = resolveAssetUrl(item.image);

  modal = document.createElement("div");
  modal.className = "quick-view-shell";
  modal.setAttribute("data-quick-view-modal", "");
  modal.innerHTML = `
    <div class="quick-view-backdrop" data-close-quick-view></div>
    <div class="quick-view-card">
      <button class="quick-view-close" type="button" data-close-quick-view>✕</button>
      <div class="quick-view-image"><img src="${escapeHtml(productImage)}" alt="${escapeHtml(item.name)}"></div>
      <div class="quick-view-details">
        <span class="eyebrow">Quick View</span>
        <h2 class="detail-title">${escapeHtml(item.name)}</h2>
        <strong class="detail-price">${formatCurrency(item.price)}</strong>
        <p class="detail-copy">${escapeHtml(item.description)}</p>
        <div class="spec-grid">
          <article class="spec-card"><span class="label">Material</span><strong>${escapeHtml(item.material)}</strong></article>
          <article class="spec-card"><span class="label">GSM</span><strong>${item.gsm} GSM</strong></article>
          <article class="spec-card"><span class="label">Fit</span><strong>${escapeHtml(item.fit_type)}</strong></article>
          <article class="spec-card"><span class="label">Neck</span><strong>${escapeHtml(item.neck_type)}</strong></article>
        </div>
        <div style="display:flex;gap:0.75rem;flex-wrap:wrap;">
          <a class="btn btn-primary" href="product.html?id=${item.id}">Full Details</a>
          <button class="btn btn-secondary" type="button" data-qv-add data-product-id="${item.id}">Add to Cart</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  document.body.classList.add("modal-open");

  modal.querySelectorAll("[data-close-quick-view]").forEach((el) => {
    el.addEventListener("click", () => { modal.remove(); document.body.classList.remove("modal-open"); });
  });

  const addBtn = modal.querySelector("[data-qv-add]");
  if (addBtn) {
    addBtn.addEventListener("click", () => {
      const size = item.sizes?.[0] || "M";
      addCartItem(item, { size });
      showToast(`${item.name} (${size}) added to cart.`);
      addBtn.textContent = "Added ✓";
      window.setTimeout(() => { addBtn.textContent = "Add to Cart"; }, 1200);
    });
  }
}

/* ───────── Navigation ───────── */

function setActiveNav() {
  const currentPage = document.body.dataset.page;
  document.querySelectorAll("[data-nav-link]").forEach((link) => {
    link.classList.toggle("is-active", link.dataset.navLink === currentPage);
  });
}

function setCartCount(count) {
  document.querySelectorAll("[data-cart-count]").forEach((badge) => { badge.textContent = String(count); });
}

function ensureAuthLinks() {
  document.querySelectorAll(".header-tools").forEach((container) => {
    const loginLink = container.querySelector("[data-login-link]");
    if (!loginLink || container.querySelector("[data-register-link]")) {
      return;
    }

    const registerLink = document.createElement("a");
    registerLink.className = "utility-pill";
    registerLink.href = "register.html";
    registerLink.textContent = "Register";
    registerLink.setAttribute("data-register-link", "");

    const cartLink = Array.from(container.querySelectorAll("a")).find((link) => link.getAttribute("href") === "cart.html");
    const logoutButton = container.querySelector("[data-logout-button]");
    container.insertBefore(registerLink, cartLink || logoutButton || null);
  });
}

function setAccountUi() {
  ensureAuthLinks();
  const firstName = currentUser?.name?.split(" ")[0] || "Member";

  document.querySelectorAll("[data-login-link]").forEach((loginLink) => {
    if (!currentUser) {
      loginLink.innerHTML = `<i class="fa-sharp-duotone fa-solid fa-arrow-right-to-bracket"></i>`;
      loginLink.setAttribute("href", "login.html");
      loginLink.classList.remove("is-greeting");
      loginLink.removeAttribute("title");
      return;
    }

    // Still include the icon for logged in state, but remove "Hello, Name"
    loginLink.innerHTML = `<i class="fa-sharp-duotone fa-solid fa-user"></i>`;
    loginLink.setAttribute("href", currentUser.role === "admin" ? "admin.html" : "products.html");
    loginLink.classList.add("is-greeting");
    loginLink.setAttribute("title", `Signed in as ${currentUser.name}`);
  });

  document.querySelectorAll("[data-register-link]").forEach((registerLink) => {
    registerLink.hidden = Boolean(currentUser);
    registerLink.innerHTML = `<i class="fa-solid fa-user-plus"></i>`;
    registerLink.setAttribute("title", "Register");
    registerLink.setAttribute("href", "register.html");
  });

  document.querySelectorAll("[data-logout-button]").forEach((logoutButton) => {
    logoutButton.hidden = !currentUser;
    logoutButton.innerHTML = `<i class="fa-sharp-duotone fa-solid fa-arrow-left-from-bracket"></i>`;
    logoutButton.setAttribute("title", "Logout");
  });

  document.querySelectorAll("[data-admin-link]").forEach((adminLink) => {
    adminLink.hidden = !(currentUser && currentUser.role === "admin");
  });
}

function bindMobileMenu() {
  const toggle = document.querySelector("[data-mobile-toggle]");
  const nav = document.querySelector("[data-mobile-nav]");
  if (!toggle || !nav) return;
  toggle.addEventListener("click", () => nav.classList.toggle("is-open"));
  nav.querySelectorAll("a").forEach((link) => { link.addEventListener("click", () => nav.classList.remove("is-open")); });
}

function bindLogout() {
  document.querySelectorAll("[data-logout-button]").forEach((button) => {
    if (button.dataset.logoutBound === "true") {
      return;
    }

    button.dataset.logoutBound = "true";
    button.addEventListener("click", async () => {
      try {
        await post("/api/auth/logout", {});
        clearAuthSession();
        currentUser = null;
        setAccountUi();
        window.setTimeout(() => {
          window.location.href = "login.html";
        }, 120);
      } catch (error) {
        showToast(error.message, "error");
      }
    });
  });
}

/* ───────── Search ───────── */

let searchProducts = [];
let searchLoadedOnce = false;

async function ensureSearchProducts() {
  if (searchLoadedOnce) return;
  try {
    const data = await get("/api/products");
    searchProducts = (Array.isArray(data) ? data : data.products || []).map(normalizeProduct);
    searchLoadedOnce = true;
  } catch { searchProducts = []; }
}

function bindSearch() {
  const input = document.querySelector("[data-search-input]");
  const dropdown = document.querySelector("[data-search-results]");
  if (!input || !dropdown) return;

  let debounce = null;
  input.addEventListener("focus", ensureSearchProducts);
  input.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(() => {
      const query = input.value.trim().toLowerCase();
      if (query.length < 2) { dropdown.hidden = true; return; }
      const matches = searchProducts.filter((p) =>
        p.name.toLowerCase().includes(query) || p.description.toLowerCase().includes(query)
      ).slice(0, 6);

      if (!matches.length) { 
        dropdown.innerHTML = '<div class="search-no-results">No products found for "' + escapeHtml(query) + '"</div>'; 
        dropdown.hidden = false; 
        return; 
      }
      
      dropdown.innerHTML = matches.map((p) => `
        <a class="search-result-item" href="product.html?id=${p.id}">
          <img class="search-result-thumb" src="${resolveAssetUrl(p.image)}" alt="${escapeHtml(p.name)}">
          <div class="search-result-info">
            <span class="search-result-name">${escapeHtml(p.name)}</span>
            <span class="search-result-price">${formatCurrency(p.price)}</span>
          </div>
        </a>
      `).join("");
      dropdown.hidden = false;
    }, 300);
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-search-wrapper]")) dropdown.hidden = true;
  });
}

/* ───────── Loaders & Skeletons ───────── */

export function startGlobalLoader() {
  if (document.querySelector(".global-loader")) return;
  const loader = document.createElement("div");
  loader.className = "global-loader";
  loader.innerHTML = '<div class="spinner"></div>';
  document.body.appendChild(loader);
}

export function endGlobalLoader() {
  const loader = document.querySelector(".global-loader");
  if (loader) {
    loader.style.opacity = "0";
    setTimeout(() => loader.remove(), 300);
  }
}



/* ───────── Back to Top ───────── */

function initBackToTop() {
  const btn = document.querySelector("[data-back-to-top]");
  if (!btn) return;
  window.addEventListener("scroll", () => { btn.classList.toggle("is-visible", window.scrollY > 400); }, { passive: true });
  btn.addEventListener("click", () => { window.scrollTo({ top: 0, behavior: "smooth" }); });
}

/* ───────── Scroll Reveal ───────── */

export function observeReveals(root = document) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add("is-visible"); observer.unobserve(entry.target); }
    });
  }, { threshold: 0.08, rootMargin: "0px 0px -40px 0px" });
  root.querySelectorAll(".reveal, .reveal-left, .reveal-right, .reveal-scale").forEach((el) => observer.observe(el));
}

/* ───────── Progress bar ───────── */

function createProgressBar() {
  let bar = document.querySelector("[data-progress-bar]");
  if (!bar) { bar = document.createElement("div"); bar.className = "progress-bar"; bar.setAttribute("data-progress-bar", ""); document.body.prepend(bar); }
  return bar;
}

export function startProgress() { const bar = createProgressBar(); bar.classList.remove("is-done"); bar.classList.add("is-active"); }
export function endProgress() { const bar = createProgressBar(); bar.classList.remove("is-active"); bar.classList.add("is-done"); window.setTimeout(() => bar.classList.remove("is-done"), 700); }

/* ───────── Newsletter ───────── */

function bindNewsletter() {
  const form = document.querySelector("[data-newsletter-form]");
  if (!form) return;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const email = form.querySelector("input[type='email']");
    if (email && email.value.trim()) { showToast("Thanks for subscribing!"); email.value = ""; }
  });
}

/* ───────── Auth state ───────── */

export async function refreshAuthState() {
  const session = getAuthSession();
  currentUser = session?.user || null;
  setAccountUi();
  if (!session?.token) return currentUser;
  try {
    const data = await get("/api/auth/me");
    if (!data?.authenticated || !data.user) {
      clearAuthSession();
      currentUser = null;
    } else {
      currentUser = data.user;
      saveAuthSession({ ...session, user: currentUser });
    }
  } catch {
    clearAuthSession();
    currentUser = null;
  }
  setAccountUi();
  return currentUser;
}

export function getCurrentUser() { return currentUser; }

/* ───────── Init ───────── */

export async function initSite() {
  setActiveNav();
  
  const user = getCurrentUser();
  if (user) {
    try {
      const items = await get("/api/wishlist");
      if (items && Array.isArray(items)) {
        items.forEach(w => localWishlist.add(Number(w.product_id)));
      }
    } catch (_) {}
  }
  bindMobileMenu();
  bindLogout();
  bindSearch();
  bindNewsletter();
  initBackToTop();
  setCartCount(getCartCount(loadCart()));
  window.addEventListener("trident:cart-change", (event) => { setCartCount(event.detail.count); });
  
  // Initialize Global Chat Widget
  import("./chat.js").then(m => m.initChatWidget());
  syncCart();
  observeReveals();
  refreshAuthState(); // Not awaited to prevent blocking
}
