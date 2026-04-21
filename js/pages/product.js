import { getWithFallback } from "../shared/api.js?v=7";
import {
  formatCurrency,
  escapeHtml,
  initSite,
  showToast,
  resolveAssetUrl,
  productCardMarkup,
  bindProductCardActions,
  promptLoginOverlay,
} from "../shared/site.js?v=7";
import { addCartItem } from "../shared/cart.js?v=7";
import { normalizeProduct } from "../shared/catalog.js?v=7";

/* ─── Recently viewed ─── */
const RV_KEY = "trident_recently_viewed";
const RV_MAX = 8;

function saveRecentlyViewed(product) {
  try {
    const item = {
      id: product.id,
      name: product.name,
      price: product.price,
      image: product.image,
      category: product.category,
      stock: product.stock,
    };
    let list = JSON.parse(localStorage.getItem(RV_KEY) || "[]");
    list = list.filter(p => String(p.id) !== String(product.id)); // dedupe
    list.unshift(item);
    if (list.length > RV_MAX) list = list.slice(0, RV_MAX);
    localStorage.setItem(RV_KEY, JSON.stringify(list));
  } catch (_) {}
}

let currentProduct = null;

async function loadProductDetail() {
  const urlParams = new URLSearchParams(window.location.search);
  const idStr = urlParams.get("id");
  const fallbackId = parseInt(idStr, 10);

  const statusContainer = document.getElementById("product-status");
  const contentContainer = document.getElementById("product-container");

  if (!idStr || isNaN(fallbackId)) {
    statusContainer.innerHTML = '<p style="color:var(--danger); font-weight:bold;">Product not found or invalid ID.</p><a href="products.html" class="btn btn-outline" style="margin-top:1rem;">Back to Shop</a>';
    return;
  }

  try {
    let product = null;
    try {
      const res = await getWithFallback(["/api/products/" + fallbackId]);
      if (res && res.product) product = res.product;
    } catch {
      const all = await getWithFallback(["/db/products.json", "/api/products"]);
      const arr = Array.isArray(all) ? all : all.products || [];
      product = arr.find(p => String(p.id) === String(fallbackId));
    }

    if (!product) {
      statusContainer.innerHTML = '<p style="color:var(--danger); font-weight:bold;">Product not found.</p><a href="products.html" class="btn btn-outline" style="margin-top:1rem;">Back to Shop</a>';
      return;
    }

    currentProduct = product;

    // Track as recently viewed
    saveRecentlyViewed(product);

    // Populate data
    document.getElementById("breadcrumb-product-name").textContent = product.name;
    document.getElementById("detail-name").textContent = product.name;
    document.getElementById("detail-category").textContent = (product.category || "T-Shirt").toUpperCase();
    document.getElementById("detail-price").textContent = formatCurrency(product.price);
    document.getElementById("detail-description").textContent = product.description || "Premium quality product from TridentWear.";
    document.getElementById("detail-main-image").src = resolveAssetUrl(product.image);

    // Update page title
    document.title = `${product.name} | TridentWear`;

    // Stock
    const detailStockBadge = document.getElementById("detail-stock-badge");
    const detailStockCount = document.getElementById("detail-stock-count");
    const addCartBtn = document.getElementById("detail-add-cart");

    if (product.stock > 0) {
      detailStockCount.textContent = product.stock;
    } else {
      detailStockBadge.innerHTML = "Out of Stock";
      detailStockBadge.style.background = "#fef2f2";
      detailStockBadge.style.color = "#991b1b";
      addCartBtn.disabled = true;
      addCartBtn.textContent = "Out of Stock";
    }

    // Sizes
    const sizeContainer = document.getElementById("detail-sizes");
    const sizes = product.sizes || ["S", "M", "L", "XL", "XXL"];
    sizeContainer.innerHTML = sizes.map((size, index) =>
      `<button class="size-btn ${index === 0 ? "is-selected" : ""}" data-size="${escapeHtml(size)}">${escapeHtml(size)}</button>`
    ).join("");

    sizeContainer.addEventListener("click", (e) => {
      if (e.target.classList.contains("size-btn")) {
        sizeContainer.querySelectorAll(".size-btn").forEach(b => b.classList.remove("is-selected"));
        e.target.classList.add("is-selected");
      }
    });

    // ── REAL Add to Cart ──
    addCartBtn.addEventListener("click", () => {
      const selectedSize = sizeContainer.querySelector(".size-btn.is-selected")?.dataset.size || "M";
      const item = normalizeProduct(product);
      try {
        addCartItem(item, { size: selectedSize, qty: 1 });
        showToast(`${escapeHtml(product.name)} (${selectedSize}) added to cart!`, "success");
        // Animate button
        addCartBtn.innerHTML = '<i class="fa-solid fa-check"></i> Added!';
        setTimeout(() => {
          addCartBtn.innerHTML = '<i class="fa-solid fa-cart-shopping"></i> Add to Cart';
        }, 1500);
      } catch (_) {
        // Not logged in
        promptLoginOverlay();
      }
    });

    // Wishlist
    document.getElementById("detail-wishlist").addEventListener("click", (e) => {
      const btn = e.currentTarget;
      btn.classList.toggle("is-wishlisted");
      const added = btn.classList.contains("is-wishlisted");
      btn.innerHTML = `<i class="${added ? "fa-solid" : "fa-regular"} fa-heart"></i>`;
      btn.style.color = added ? "var(--primary)" : "inherit";
      showToast(added ? "Added to wishlist" : "Removed from wishlist", "info");
    });

    // Reveal
    statusContainer.style.display = "none";
    contentContainer.style.display = "grid";

    // Load related after revealing
    loadRelatedProducts(product);

  } catch (err) {
    console.error("Error loading product detail:", err);
    statusContainer.innerHTML = '<p style="color:var(--danger); font-weight:bold;">Failed to load product details.</p><a href="products.html" class="btn btn-outline" style="margin-top:1rem;">Back to Shop</a>';
  }
}

/* ─── You May Also Like ─── */
async function loadRelatedProducts(currentProd) {
  const grid = document.getElementById("related-products-grid");
  if (!grid) return;

  try {
    const data = await getWithFallback(["/api/products"]);
    const all = (Array.isArray(data) ? data : data.products || []);

    // Same category, exclude current
    let related = all.filter(p => p.category === currentProd.category && String(p.id) !== String(currentProd.id));

    // Fallback to random if not enough
    if (related.length < 4) {
      const others = all.filter(p => String(p.id) !== String(currentProd.id));
      related = [...related, ...others].slice(0, 4);
    } else {
      // Shuffle and pick 4
      related = related.sort(() => 0.5 - Math.random()).slice(0, 4);
    }

    if (!related.length) return;

    grid.innerHTML = related.map(productCardMarkup).join("");
    bindProductCardActions(grid, related);
  } catch (e) {
    console.warn("Could not load related products", e);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  await loadProductDetail();
});
