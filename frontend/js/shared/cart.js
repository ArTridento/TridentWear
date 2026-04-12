const STORAGE_KEY = "trident-premium-cart";

function emitChange(items) {
  window.dispatchEvent(
    new CustomEvent("trident:cart-change", {
      detail: {
        items,
        count: getCartCount(items),
        subtotal: getCartSubtotal(items),
      },
    }),
  );
}

export function loadCart() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveCart(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  emitChange(items);
  return items;
}

export function syncCart() {
  emitChange(loadCart());
}

export function getCartCount(items = loadCart()) {
  return items.reduce((total, item) => total + Number(item.qty || 0), 0);
}

export function getCartSubtotal(items = loadCart()) {
  return items.reduce((total, item) => total + Number(item.price || 0) * Number(item.qty || 0), 0);
}

export function addCartItem(product, options = {}) {
  const size = options.size || product.sizes?.[0] || "M";
  const qty = Math.max(Number(options.qty || 1), 1);
  const items = loadCart();
  const existing = items.find((item) => item.id === product.id && item.size === size);

  if (existing) {
    existing.qty += qty;
  } else {
    items.push({
      id: product.id,
      name: product.name,
      price: product.price,
      image: product.image,
      size,
      qty,
    });
  }

  return saveCart(items);
}

export function updateCartItemQuantity(id, size, nextQty) {
  const items = loadCart()
    .map((item) =>
      item.id === id && item.size === size
        ? {
            ...item,
            qty: Math.max(nextQty, 0),
          }
        : item,
    )
    .filter((item) => item.qty > 0);

  return saveCart(items);
}

export function removeCartItem(id, size) {
  return saveCart(loadCart().filter((item) => !(item.id === id && item.size === size)));
}

export function clearCart() {
  return saveCart([]);
}
