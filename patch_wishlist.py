import re

FILE_PATH = r"d:\TridentWear\frontend\js\shared\site.js"

with open(FILE_PATH, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Replace wishlist functions
wishlist_old = """const WISHLIST_KEY = "trident-wishlist";

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
}"""

wishlist_new = """export const localWishlist = new Set();

export function isWishlisted(id) {
  return localWishlist.has(Number(id));
}

export async function toggleWishlist(id) {
  const numId = Number(id);
  const user = getCurrentUser();
  if (!user) {
    showToast("Please login to use wishlist.", "error");
    window.location.href = "/login?next=/wishlist";
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
}"""

# Normalize DOS line endings if present in text and pattern
normalized_text = text.replace('\\r\\n', '\\n')
res1 = normalized_text.replace(wishlist_old.replace('\\r\\n', '\\n'), wishlist_new)

# 2. Add fetching to initSite
init_old = """export async function initSite() {
  setActiveNav();"""
init_new = """export async function initSite() {
  setActiveNav();
  await refreshUser();
  const user = getCurrentUser();
  if (user) {
    try {
      const items = await get("/api/wishlist");
      if (items && Array.isArray(items)) {
        items.forEach(w => localWishlist.add(Number(w.product_id)));
      }
    } catch (_) {}
  }"""

res2 = res1.replace(init_old.replace('\\r\\n', '\\n'), init_new)

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(res2)

print("Patch applied to site.js")
