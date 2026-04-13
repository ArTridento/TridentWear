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

export function createEmptyMarkup(title, copy, href = "/products", label = "Browse Products") {
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
      <a class="product-media" href="/product?id=${item.id}">
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
            <a class="btn btn-outline" href="/product?id=${item.id}">View</a>
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
      addCartItem(product, { size: defaultSize });
      showToast(`${product.name} (${defaultSize}) added to cart.`);
      button.textContent = "Added ✓";
      window.setTimeout(() => { button.textContent = "Add to Cart"; }, 1200);
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

const WISHLIST_KEY = "trident-wishlist";

function loadWishlist() {
  try { return JSON.parse(localStorage.getItem(WISHLIST_KEY) || "[]"); }
  catch { return []; }
}

function saveWishlist(ids) { localStorage.setItem(WISHLIST_KEY, JSON.stringify(ids)); }
function isWishlisted(id) { return loadWishlist().includes(Number(id)); }

function toggleWishlist(id) {
  const ids = loadWishlist();
  const numId = Number(id);
  const index = ids.indexOf(numId);
  if (index === -1) ids.push(numId); else ids.splice(index, 1);
  saveWishlist(ids);
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
          <a class="btn btn-primary" href="/product?id=${item.id}">Full Details</a>
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

function setAccountUi() {
  const accountLink = document.querySelector("[data-account-link]");
  const logoutButton = document.querySelector("[data-logout-button]");
  const adminLink = document.querySelector("[data-admin-link]");

  if (accountLink) {
    if (!currentUser) { accountLink.textContent = "Login"; accountLink.setAttribute("href", "/auth"); }
    else if (currentUser.role === "admin") { accountLink.textContent = "Admin"; accountLink.setAttribute("href", "/admin"); }
    else { accountLink.textContent = currentUser.name.split(" ")[0]; accountLink.setAttribute("href", "/auth"); }
  }
  if (logoutButton) logoutButton.hidden = !currentUser;
  if (adminLink) adminLink.hidden = !(currentUser && currentUser.role === "admin");
}

function bindMobileMenu() {
  const toggle = document.querySelector("[data-mobile-toggle]");
  const nav = document.querySelector("[data-mobile-nav]");
  if (!toggle || !nav) return;
  toggle.addEventListener("click", () => nav.classList.toggle("is-open"));
  nav.querySelectorAll("a").forEach((link) => { link.addEventListener("click", () => nav.classList.remove("is-open")); });
}

function bindLogout() {
  const button = document.querySelector("[data-logout-button]");
  if (!button) return;
  button.addEventListener("click", async () => {
    try {
      await post("/api/auth/logout", {});
      clearAuthSession();
      currentUser = null;
      setAccountUi();
      showToast("Signed out successfully.");
      if (document.body.dataset.page === "admin") window.location.href = "/auth";
    } catch (error) { showToast(error.message, "error"); }
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
        p.name.toLowerCase().includes(query) || p.description.toLowerCase().includes(query) || p.tag?.toLowerCase().includes(query)
      ).slice(0, 6);

      if (!matches.length) { dropdown.innerHTML = '<div class="search-no-results">No products found.</div>'; dropdown.hidden = false; return; }
      dropdown.innerHTML = matches.map((p) => `
        <a class="search-result-item" href="/product?id=${p.id}">
          <img class="search-result-thumb" src="${resolveAssetUrl(p.image)}" alt="${escapeHtml(p.name)}">
          <div class="search-result-info">
            <span class="search-result-name">${escapeHtml(p.name)}</span>
            <span class="search-result-price">${formatCurrency(p.price)}</span>
          </div>
        </a>
      `).join("");
      dropdown.hidden = false;
    }, 250);
  });

  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-search-wrapper]")) dropdown.hidden = true;
  });
}

/* ───────── Back to Top ───────── */

function initBackToTop() {
  const btn = document.querySelector("[data-back-to-top]");
  if (!btn) return;
  window.addEventListener("scroll", () => { btn.classList.toggle("is-visible", window.scrollY > 400); }, { passive: true });
  btn.addEventListener("click", () => { window.scrollTo({ top: 0, behavior: "smooth" }); });
}

/* ───────── Scroll Reveal ───────── */

function observeReveals(root = document) {
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
    currentUser = data.user;
    saveAuthSession({ ...session, user: currentUser });
  } catch { clearAuthSession(); currentUser = null; }
  setAccountUi();
  return currentUser;
}

export function getCurrentUser() { return currentUser; }

/* ───────── Init ───────── */

export async function initSite() {
  setActiveNav();
  bindMobileMenu();
  bindLogout();
  bindSearch();
  bindNewsletter();
  initBackToTop();
  setCartCount(getCartCount(loadCart()));
  window.addEventListener("trident:cart-change", (event) => { setCartCount(event.detail.count); });
  syncCart();
  observeReveals();
  await refreshAuthState();
}
