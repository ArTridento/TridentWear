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
  const imagesJson = JSON.stringify(product.images || [item.image]);
  const wishlisted = isWishlisted(item.id);
  const subcategoryLabel = product.subcategory ? product.subcategory.replace(/-/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') : 'T-Shirt';

  return `
    <article class="product-card reveal" data-product-card data-product-id="${item.id}">
      <div class="product-media" data-product-hover-gallery data-images='${escapeHtml(imagesJson)}'>
        <img src="${escapeHtml(productImage)}" alt="${escapeHtml(item.name)}" loading="lazy" class="product-image">
        <div class="product-media-overlay">
          <span class="hover-hint">Hover for more</span>
        </div>
        <button class="wishlist-btn${wishlisted ? " is-wishlisted" : ""}" type="button" data-wishlist-toggle data-product-id="${item.id}" aria-label="Toggle wishlist">
          <svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
        </button>
      </div>
      <div class="product-body">
        <span class="product-type">${escapeHtml(subcategoryLabel)}</span>
        <h3 class="product-name">${escapeHtml(item.name)}</h3>
        <div class="product-footer">
          <strong class="product-price">${formatCurrency(item.price)}</strong>
        </div>
      </div>
    </article>
  `;
}

/* ───────── Bind product card actions ───────── */

export function bindProductCardActions(container, products) {
  const lookup = new Map(products.map((product) => {
    const item = normalizeProduct(product);
    return [String(item.id), product];
  }));

  // Hover image cycling
  container.querySelectorAll("[data-product-hover-gallery]").forEach((gallery) => {
    const imageElement = gallery.querySelector(".product-image");
    try {
      const images = JSON.parse(gallery.dataset.images);
      let currentIndex = 0;
      
      gallery.addEventListener("mouseenter", () => {
        const cycleInterval = setInterval(() => {
          if (!gallery.matches(":hover")) {
            clearInterval(cycleInterval);
            return;
          }
          currentIndex = (currentIndex + 1) % images.length;
          imageElement.style.opacity = "0.7";
          setTimeout(() => {
            imageElement.src = images[currentIndex];
            imageElement.style.opacity = "1";
          }, 150);
        }, 800);
        
        gallery._cycleInterval = cycleInterval;
      });
      
      gallery.addEventListener("mouseleave", () => {
        if (gallery._cycleInterval) clearInterval(gallery._cycleInterval);
        currentIndex = 0;
        imageElement.src = images[0];
      });
    } catch (e) {
      console.warn("Could not parse images", e);
    }
  });

  // Click to open product detail
  container.querySelectorAll("[data-product-card]").forEach((card) => {
    card.addEventListener("click", (event) => {
      if (event.target.closest("[data-wishlist-toggle]")) return;
      event.preventDefault();
      event.stopPropagation();
      const productId = card.dataset.productId;
      const product = lookup.get(productId);
      if (product) openProductDetail(product);
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

  observeReveals(container);
}

// Product detail modal
function openProductDetail(product) {
  const modal = document.createElement("div");
  modal.className = "product-detail-modal";
  const images = [product.image, ...(product.images || [])].filter((v, i, a) => v && a.indexOf(v) === i);
  const typeLabel = (product.subcategory || '').replace(/-/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ') || 'T-Shirt';

  modal.innerHTML = `
    <div class="product-detail-backdrop"></div>
    <div class="product-detail-content">
      <button class="product-detail-close" type="button" aria-label="Close">&#x2715;</button>

      <div class="product-detail-gallery">
        <div class="product-detail-main-image">
          <img src="${resolveAssetUrl(product.image)}" alt="${escapeHtml(product.name)}" id="detail-main-image">
        </div>
        ${images.length > 1 ? `<div class="product-detail-thumbnails">${images.map((img, i) => `<button class="detail-thumbnail ${i === 0 ? 'is-active' : ''}" data-image="${escapeHtml(img)}" style="background-image:url('${resolveAssetUrl(img)}')"></button>`).join('')}</div>` : ''}
      </div>

      <div class="product-detail-info">
        <div class="detail-header">
          <h2 class="detail-name">${escapeHtml(product.name)}</h2>
          <span class="detail-type">${escapeHtml(typeLabel)}</span>
        </div>
        <hr class="detail-divider">
        <div class="detail-price-block">
          <strong class="detail-price">${formatCurrency(product.price)}</strong>
          <span class="detail-price-note">Price incl. of all taxes</span>
        </div>
        <div class="detail-selection-row" style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
          <div class="detail-qty-row" style="display: flex; align-items: center; gap: 0.75rem;">
            <span class="detail-qty-label" style="font-size: 0.85rem;">Quantity</span>
            <div class="detail-qty-counter">
              <button class="qty-btn qty-minus" type="button" aria-label="Decrease">&minus;</button>
              <span class="qty-value" id="detail-qty-val">0</span>
              <button class="qty-btn qty-plus" type="button" aria-label="Increase">+</button>
            </div>
          </div>
          <div class="detail-size-row" style="display: flex; align-items: center; gap: 0.75rem; flex: 1; justify-content: flex-end;">
            <div class="size-options">
              ${(product.sizes || ['S','M','L','XL']).filter(s => s !== 'XXL' && s !== 'XXXL').map((size, i) => `<button class="size-btn ${i === 0 ? 'is-selected' : ''}" data-size="${escapeHtml(size)}">${escapeHtml(size)}</button>`).join('')}
            </div>
          </div>
        </div>
        <div style="display: flex; justify-content: flex-end;">
          <button class="detail-size-chart-btn" type="button" data-size-chart>SIZE CHART</button>
        </div>
        <div class="detail-size-chart-panel" hidden>
          <table class="size-chart-table">
            <thead><tr><th>Size</th><th>Chest (in)</th><th>Length (in)</th></tr></thead>
            <tbody>
              <tr><td>XS</td><td>36</td><td>27</td></tr>
              <tr><td>S</td><td>38</td><td>28</td></tr>
              <tr><td>M</td><td>40</td><td>29</td></tr>
              <tr><td>L</td><td>42</td><td>30</td></tr>
              <tr><td>XL</td><td>44</td><td>31</td></tr>
              <tr><td>XXL</td><td>46</td><td>32</td></tr>
              <tr><td>XXXL</td><td>48</td><td>33</td></tr>
            </tbody>
          </table>
        </div>
        <div class="detail-cta-row">
          <button class="detail-icon-btn detail-add-to-cart" type="button" data-product-id="${product.id}" title="Add to Cart" aria-label="Add to Cart"><i class="fa-solid fa-cart-shopping"></i></button>
          <button class="detail-icon-btn detail-wishlist-btn" type="button" data-product-id="${product.id}" title="Add to Wishlist" aria-label="Add to Wishlist"><i class="fa-regular fa-heart"></i></button>
          <button class="detail-icon-btn detail-buy-now" type="button" data-product-id="${product.id}" title="Buy Now" aria-label="Buy Now"><i class="fa-solid fa-bolt"></i></button>
        </div>
        <div class="detail-delivery">
          <strong class="detail-delivery-title">Delivery Details</strong>
          <div class="detail-pincode-row">
            <input class="detail-pincode-input" type="text" placeholder="Enter Pincode" maxlength="6" inputmode="numeric">
            <button class="detail-pincode-check" type="button">CHECK</button>
          </div>
          <div class="detail-pincode-result" hidden></div>
        </div>
        <div class="detail-return-note">
          <i class="fa-solid fa-rotate-left"></i>
          <span>Eligible for <strong>30-day return or exchange</strong>. No questions asked.</span>
        </div>
        <div class="detail-accordions">
          <div class="detail-accordion">
            <button class="detail-accordion-header" type="button" data-accordion>
              <span>Product Details</span><i class="fa-solid fa-chevron-down detail-accordion-icon"></i>
            </button>
            <div class="detail-accordion-body" hidden>
              <dl class="detail-spec-list">
                <dt>Material</dt><dd>${escapeHtml(product.material || 'Cotton')}</dd>
                <dt>GSM</dt><dd>${product.gsm || 220} GSM</dd>
                <dt>Fit Type</dt><dd>${escapeHtml(product.fit_type || 'Regular Fit')}</dd>
                <dt>Neck Type</dt><dd>${escapeHtml(product.neck_type || 'Round Neck')}</dd>
              </dl>
            </div>
          </div>
          <div class="detail-accordion">
            <button class="detail-accordion-header" type="button" data-accordion>
              <span>Product Description</span><i class="fa-solid fa-chevron-down detail-accordion-icon"></i>
            </button>
            <div class="detail-accordion-body" hidden>
              <p>${escapeHtml(product.description || 'No description available.')}</p>
            </div>
          </div>
          <div class="detail-accordion">
            <button class="detail-accordion-header" type="button" data-accordion>
              <span>Artist's Details</span><i class="fa-solid fa-chevron-down detail-accordion-icon"></i>
            </button>
            <div class="detail-accordion-body" hidden>
              <p>${escapeHtml(product.artist_details || 'Designed by the TridentWear in-house design team. Inspired by Indian heritage, culture, and street fashion.')}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  document.body.classList.add("modal-open");
  const closeModal = () => { modal.remove(); document.body.classList.remove("modal-open"); };

  // Image gallery
  modal.querySelectorAll(".detail-thumbnail").forEach(btn => {
    btn.addEventListener("click", () => {
      const mainImg = modal.querySelector("#detail-main-image");
      mainImg.style.opacity = "0.5";
      setTimeout(() => { mainImg.src = resolveAssetUrl(btn.dataset.image); mainImg.style.opacity = "1"; }, 150);
      modal.querySelectorAll(".detail-thumbnail").forEach(b => b.classList.remove("is-active"));
      btn.classList.add("is-active");
    });
  });

  // Size
  let selectedSize = product.sizes?.[0] || 'M';
  modal.querySelectorAll(".size-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      modal.querySelectorAll(".size-btn").forEach(b => b.classList.remove("is-selected"));
      btn.classList.add("is-selected");
      selectedSize = btn.dataset.size;
    });
  });

  // Qty counter
  let qty = 0;
  const qtyValEl = modal.querySelector("#detail-qty-val");
  modal.querySelector(".qty-plus").addEventListener("click", () => { qty++; qtyValEl.textContent = qty; });
  modal.querySelector(".qty-minus").addEventListener("click", () => { if (qty > 0) qty--; qtyValEl.textContent = qty; });
  const getQty = () => Math.max(1, qty);

  // Add to cart
  modal.querySelector(".detail-add-to-cart").addEventListener("click", () => {
    try {
      const q = getQty();
      for (let i = 0; i < q; i++) addCartItem(product, { size: selectedSize });
      showToast(`${product.name} (${selectedSize}) \xd7${q} added to cart.`);
      closeModal();
    } catch (err) { showToast(err.message, "error"); }
  });

  // Buy Now
  modal.querySelector(".detail-buy-now").addEventListener("click", () => {
    try {
      const q = getQty();
      for (let i = 0; i < q; i++) addCartItem(product, { size: selectedSize });
      closeModal();
      window.location.href = "checkout.html";
    } catch (err) { showToast(err.message, "error"); }
  });

  // Wishlist
  modal.querySelector(".detail-wishlist-btn").addEventListener("click", async (e) => {
    const btn = e.currentTarget;
    try {
      await toggleWishlist(product.id);
      const wished = localWishlist.has(Number(product.id));
      btn.classList.toggle("is-wishlisted", wished);
      btn.querySelector("i").className = wished ? "fa-solid fa-heart" : "fa-regular fa-heart";
      if (wished) showToast(`${product.name} added to wishlist.`);
    } catch (err) { if (err.message !== "unauthorized") showToast(err.message, "error"); }
  });

  // Pincode
  modal.querySelector(".detail-pincode-check").addEventListener("click", () => {
    const input = modal.querySelector(".detail-pincode-input");
    const result = modal.querySelector(".detail-pincode-result");
    const pin = input.value.trim();
    result.textContent = /^\d{6}$/.test(pin)
      ? `\u2713 Delivery available to ${pin}. Estimated 3\u20135 business days.`
      : "Please enter a valid 6-digit pincode.";
    result.className = `detail-pincode-result ${/^\d{6}$/.test(pin) ? 'is-success' : 'is-error'}`;
    result.hidden = false;
  });

  // Size chart toggle (inline)
  const sizeChartBtn = modal.querySelector("[data-size-chart]");
  const sizeChartPanel = modal.querySelector(".detail-size-chart-panel");
  sizeChartBtn?.addEventListener("click", () => {
    sizeChartPanel.hidden = !sizeChartPanel.hidden;
    sizeChartBtn.textContent = sizeChartPanel.hidden ? "SIZE CHART" : "HIDE CHART";
  });

  // Accordions
  modal.querySelectorAll("[data-accordion]").forEach(btn => {
    btn.addEventListener("click", () => {
      const body = btn.nextElementSibling;
      body.hidden = !body.hidden;
      btn.querySelector(".detail-accordion-icon").style.transform = body.hidden ? "" : "rotate(180deg)";
    });
  });

  modal.querySelector(".product-detail-close").addEventListener("click", closeModal);
  modal.querySelector(".product-detail-backdrop").addEventListener("click", closeModal);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeModal(); }, { once: true });
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
    window.location.href = "login.html?next=wishlist.html";
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
  
  /* Set active bottom nav item */
  const navMap = {
    home: "home",
    products: "shop",
    product: "shop",
    cart: "cart",
    wishlist: "wishlist",
    about: "home",
    contact: "home",
  };
  
  const bottomNav = document.querySelector(".bottom-nav");
  if (bottomNav) {
    const page = navMap[currentPage] || currentPage;
    bottomNav.querySelectorAll("[data-nav]").forEach((item) => {
      item.classList.toggle("is-active", item.dataset.nav === page);
    });
  }
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

  const mobileQuery = window.matchMedia("(max-width: 56rem)");
  const dropdowns = Array.from(nav.querySelectorAll(".nav-dropdown"));
  const setExpanded = (element, expanded) => {
    element?.setAttribute("aria-expanded", String(Boolean(expanded)));
  };

  const closeMenu = () => {
    nav.classList.remove("is-open");
    setExpanded(toggle, false);
    dropdowns.forEach((dropdown) => {
      dropdown.classList.remove("is-open");
      setExpanded(dropdown.querySelector(".nav-dropdown-trigger"), false);
    });
  };

  toggle.setAttribute("aria-expanded", "false");
  toggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    setExpanded(toggle, isOpen);
  });

  dropdowns.forEach((dropdown) => {
    const trigger = dropdown.querySelector(".nav-dropdown-trigger");
    if (!trigger) return;
    trigger.setAttribute("aria-expanded", "false");
    trigger.addEventListener("click", (event) => {
      if (!mobileQuery.matches) return;
      event.preventDefault();
      const willOpen = !dropdown.classList.contains("is-open");
      dropdowns.forEach((item) => {
        if (item !== dropdown) {
          item.classList.remove("is-open");
          setExpanded(item.querySelector(".nav-dropdown-trigger"), false);
        }
      });
      dropdown.classList.toggle("is-open", willOpen);
      setExpanded(trigger, willOpen);
    });
  });

  nav.querySelectorAll("a").forEach((link) => {
    if (link.classList.contains("nav-dropdown-trigger")) return;
    link.addEventListener("click", closeMenu);
  });

  document.addEventListener("click", (event) => {
    if (mobileQuery.matches && !event.target.closest("[data-mobile-nav]") && !event.target.closest("[data-mobile-toggle]")) {
      closeMenu();
    }
  });

  const syncDesktopState = () => {
    if (!mobileQuery.matches) {
      closeMenu();
    }
  };

  if (typeof mobileQuery.addEventListener === "function") {
    mobileQuery.addEventListener("change", syncDesktopState);
  } else {
    mobileQuery.addListener(syncDesktopState);
  }
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
  await refreshAuthState();

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
  syncCart();
  observeReveals();
}
