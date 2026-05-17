import { getAuthSession } from "./api.js";

const GUEST_KEY = "trident-cart-guest";

function getStorageKey() {
  const session = getAuthSession();
  if (session && session.user && session.user.id) {
    return `trident-cart-${session.user.id}`;
  }
  return GUEST_KEY;
}

function emitChange(items) {
  window.dispatchEvent(
    new CustomEvent("trident:cart-change", {
      detail: {
        items,
        count: getCartCount(items),
        subtotal: getCartSubtotal(items),
        openDrawer: false,
      },
    }),
  );
}

export function loadCart() {
  try {
    const key = getStorageKey();
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveCart(items) {
  const key = getStorageKey();
  localStorage.setItem(key, JSON.stringify(items));
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

  const saved = saveCart(items);
  window.dispatchEvent(
    new CustomEvent("trident:cart-change", {
      detail: {
        items: saved,
        count: getCartCount(saved),
        subtotal: getCartSubtotal(saved),
        openDrawer: Boolean(options.openDrawer),
      },
    }),
  );
  return saved;
}

/**
 * Merge guest cart into user cart after login.
 * Call this right after a successful auth session is saved.
 */
export function mergeGuestCartOnLogin() {
  try {
    const session = getAuthSession();
    if (!session || !session.user || !session.user.id) return;

    const guestRaw = localStorage.getItem(GUEST_KEY);
    if (!guestRaw) return;

    const guestItems = JSON.parse(guestRaw);
    if (!guestItems || !guestItems.length) return;

    const userKey = `trident-cart-${session.user.id}`;
    const existingRaw = localStorage.getItem(userKey);
    const userItems = existingRaw ? JSON.parse(existingRaw) : [];

    // Merge: add guest quantities into user cart
    for (const gItem of guestItems) {
      const match = userItems.find(i => i.id === gItem.id && i.size === gItem.size);
      if (match) {
        match.qty += gItem.qty;
      } else {
        userItems.push({ ...gItem });
      }
    }

    localStorage.setItem(userKey, JSON.stringify(userItems));
    localStorage.removeItem(GUEST_KEY);
    emitChange(userItems);
  } catch (_) {}
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
