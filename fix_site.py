import re

with open(r'd:\TridentWear\frontend\js\shared\site.js', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = "    </article>\n  `;\n}"
end_marker = "/* ───────── Wishlist (localStorage) ───────── */"

idx1 = text.find(start_marker)
idx2 = text.find(end_marker)

if idx1 != -1 and idx2 != -1:
    before = text[:idx1 + len(start_marker)]
    after = text[idx2:]
    
    middle = """

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

"""
    with open(r'd:\TridentWear\frontend\js\shared\site.js', 'w', encoding='utf-8') as f:
        f.write(before + middle + after)
    print("Fixed site.js")
else:
    print("Failed to find markers")
