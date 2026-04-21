import { getWithFallback } from "../shared/api.js";
import { formatCurrency, escapeHtml, initSite, showToast, resolveAssetUrl } from "../shared/site.js";

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
    // Attempt specific fetch. 
    // Wait, the API returns {"success": true, "product": {...}}
    let product = null;
    try {
       const res = await getWithFallback(["/api/products/" + fallbackId]);
       if (res && res.product) {
         product = res.product;
       }
    } catch {
       // If API lacks single id fetching or fails, fallback to full list
       const all = await getWithFallback(["/db/products.json", "/api/products"]);
       const productsArray = Array.isArray(all) ? all : all.products || [];
       product = productsArray.find(p => String(p.id) === String(fallbackId));
    }

    if (!product) {
      statusContainer.innerHTML = '<p style="color:var(--danger); font-weight:bold;">Product not found.</p><a href="products.html" class="btn btn-outline" style="margin-top:1rem;">Back to Shop</a>';
      return;
    }

    // Populate data
    document.getElementById("breadcrumb-product-name").textContent = product.name;
    document.getElementById("detail-name").textContent = product.name;
    document.getElementById("detail-category").textContent = (product.category || 'T-Shirt').toUpperCase();
    document.getElementById("detail-price").textContent = formatCurrency(product.price);
    document.getElementById("detail-description").textContent = product.description || "Premium quality product from TridentWear.";
    document.getElementById("detail-main-image").src = resolveAssetUrl(product.image);

    // Stock
    const detailStockBadge = document.getElementById("detail-stock-badge");
    const detailStockCount = document.getElementById("detail-stock-count");
    if (product.stock > 0) {
      detailStockCount.textContent = product.stock;
    } else {
      detailStockBadge.innerHTML = "Out of Stock";
      detailStockBadge.style.background = "#fef2f2";
      detailStockBadge.style.color = "#991b1b";
      document.getElementById("detail-add-cart").disabled = true;
      document.getElementById("detail-add-cart").textContent = "Out of Stock";
    }

    // Sizes
    const sizeContainer = document.getElementById("detail-sizes");
    const sizes = product.sizes || ['S', 'M', 'L', 'XL'];
    sizeContainer.innerHTML = sizes.map((size, index) => 
      `<button class="size-btn ${index === 0 ? 'is-selected' : ''}" data-size="${escapeHtml(size)}">${escapeHtml(size)}</button>`
    ).join("");

    // Bind size selection
    sizeContainer.addEventListener("click", (e) => {
      if (e.target.classList.contains("size-btn")) {
        sizeContainer.querySelectorAll(".size-btn").forEach(b => b.classList.remove("is-selected"));
        e.target.classList.add("is-selected");
      }
    });

    // Mock cart interaction
    document.getElementById("detail-add-cart").addEventListener("click", () => {
      const selectedSize = document.querySelector(".size-btn.is-selected")?.dataset.size || "M";
      showToast(`Added ${escapeHtml(product.name)} (Size ${selectedSize}) to cart!`, "success");
    });

    document.getElementById("detail-wishlist").addEventListener("click", (e) => {
      const btn = e.currentTarget;
      btn.classList.toggle("is-wishlisted");
      const added = btn.classList.contains("is-wishlisted");
      btn.innerHTML = `<i class="${added ? 'fa-solid' : 'fa-regular'} fa-heart"></i>`;
      btn.style.color = added ? "var(--primary)" : "inherit";
      showToast(added ? "Added to wishlist" : "Removed from wishlist", "info");
    });

    // Reveal
    statusContainer.style.display = "none";
    contentContainer.style.display = "grid";

  } catch (err) {
    console.error("Error loading product detail:", err);
    statusContainer.innerHTML = '<p style="color:var(--danger); font-weight:bold;">Failed to load product details.</p><a href="products.html" class="btn btn-outline" style="margin-top:1rem;">Back to Shop</a>';
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  await loadProductDetail();
});
