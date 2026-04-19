import {
  DEFAULT_CHAT,
  DEFAULT_CONTACTS,
  DEFAULT_COUPONS,
  DEFAULT_ORDERS,
  DEFAULT_PRODUCTS,
  DEFAULT_REVIEWS,
  DEFAULT_USERS,
} from "./mock-data.js";

export const STATIC_MODE = true;

const SITE_ROOT = new URL("../../", import.meta.url);
const AUTH_STORAGE_KEY = "tridentwear-auth-session";
const STORAGE_KEYS = {
  products: "tridentwear-products-db",
  users: "tridentwear-users-db",
  orders: "tridentwear-orders-db",
  reviews: "tridentwear-reviews-db",
  contacts: "tridentwear-contacts-db",
  chat: "tridentwear-chat-db",
  coupons: "tridentwear-coupons-db",
};
const memoryStore = new Map();

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function readStorage(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) {
      const seeded = clone(fallback);
      localStorage.setItem(key, JSON.stringify(seeded));
      return seeded;
    }
    return JSON.parse(raw);
  } catch {
    if (!memoryStore.has(key)) {
      memoryStore.set(key, clone(fallback));
    }
    return clone(memoryStore.get(key));
  }
}

function writeStorage(key, value) {
  const serialized = clone(value);
  try {
    localStorage.setItem(key, JSON.stringify(serialized));
  } catch {
    memoryStore.set(key, serialized);
  }
  return clone(serialized);
}

function removeStorage(key) {
  try {
    localStorage.removeItem(key);
  } catch {
    memoryStore.delete(key);
  }
}

function nowIso() {
  return new Date().toISOString();
}

function nextNumericId(items) {
  if (!items.length) {
    return 1;
  }
  return Math.max(...items.map((item) => Number(item.id || 0))) + 1;
}

function roundCurrency(value) {
  return Math.round(Number(value || 0) * 100) / 100;
}

function normalizeImagePath(value) {
  if (!value) {
    return "/images/hero-banner.png";
  }
  if (value.startsWith("data:") || /^https?:\/\//.test(value)) {
    return value;
  }
  if (value.startsWith("/")) {
    return value;
  }
  return `/${String(value).replace(/^\.?\//, "")}`;
}

function sanitizeUser(user) {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    phone: user.phone || "",
    role: user.role || "customer",
    created_at: user.created_at,
  };
}

function createToken(user) {
  const payload = {
    sub: user.id,
    role: user.role,
    issued_at: Date.now(),
  };
  return btoa(JSON.stringify(payload)).replaceAll("=", "");
}

function getProductsDb() {
  return readStorage(STORAGE_KEYS.products, DEFAULT_PRODUCTS);
}

function saveProductsDb(products) {
  return writeStorage(STORAGE_KEYS.products, products);
}

function getUsersDb() {
  return readStorage(STORAGE_KEYS.users, DEFAULT_USERS);
}

function saveUsersDb(users) {
  return writeStorage(STORAGE_KEYS.users, users);
}

function getOrdersDb() {
  return readStorage(STORAGE_KEYS.orders, DEFAULT_ORDERS);
}

function saveOrdersDb(orders) {
  return writeStorage(STORAGE_KEYS.orders, orders);
}

function getReviewsDb() {
  return readStorage(STORAGE_KEYS.reviews, DEFAULT_REVIEWS);
}

function saveReviewsDb(reviews) {
  return writeStorage(STORAGE_KEYS.reviews, reviews);
}

function getContactsDb() {
  return readStorage(STORAGE_KEYS.contacts, DEFAULT_CONTACTS);
}

function saveContactsDb(contacts) {
  return writeStorage(STORAGE_KEYS.contacts, contacts);
}

function getChatDb() {
  return readStorage(STORAGE_KEYS.chat, DEFAULT_CHAT);
}

function saveChatDb(chat) {
  return writeStorage(STORAGE_KEYS.chat, chat);
}

function getCouponsDb() {
  return readStorage(STORAGE_KEYS.coupons, DEFAULT_COUPONS);
}

function wishlistKey(userId) {
  return `tridentwear-wishlist-${userId}`;
}

function getWishlistDb(userId) {
  return readStorage(wishlistKey(userId), []);
}

function saveWishlistDb(userId, items) {
  return writeStorage(wishlistKey(userId), items);
}

function findUserByEmail(email) {
  return getUsersDb().find((user) => user.email.toLowerCase() === String(email || "").trim().toLowerCase()) || null;
}

function findUserByPhone(phone) {
  return getUsersDb().find((user) => user.phone === String(phone || "").trim()) || null;
}

function findProductById(productId) {
  return getProductsDb().find((product) => Number(product.id) === Number(productId)) || null;
}

function getAuthUser() {
  const session = getAuthSession();
  if (!session?.user?.id) {
    return null;
  }
  return getUsersDb().find((user) => Number(user.id) === Number(session.user.id)) || null;
}

function requireUser() {
  const user = getAuthUser();
  if (!user) {
    throw createHttpError(401, "Please sign in first.");
  }
  return user;
}

function requireAdmin() {
  const user = requireUser();
  if (user.role !== "admin") {
    throw createHttpError(403, "Admin access required.");
  }
  return user;
}

function createHttpError(status, message) {
  const error = new Error(message);
  error.status = status;
  return error;
}

function validateEmail(email) {
  const normalized = String(email || "").trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(normalized)) {
    throw createHttpError(400, "Enter a valid email address.");
  }
  return normalized;
}

function createOrderId() {
  return `TRI-${Math.random().toString(16).slice(2, 10).toUpperCase()}`;
}

function createTrackingPayload(order) {
  if (!order) {
    throw createHttpError(404, "Order not found.");
  }

  if (order.tracking_id) {
    const status = order.status === "shipped" ? "In Transit" : String(order.status || "confirmed").replace(/\b\w/g, (match) => match.toUpperCase());
    return {
      status,
      courier: order.courier || "Delhivery",
      tracking_id: order.tracking_id,
      estimated_delivery: order.estimated_delivery || "Within 3-5 days",
    };
  }

  return {
    status: String(order.status || "confirmed").replace(/\b\w/g, (match) => match.toUpperCase()),
    courier: "Pending Allocation",
    tracking_id: null,
    estimated_delivery: "Tracking will be updated soon",
  };
}

function buildAnalytics(orders) {
  const totalRevenue = orders.reduce((sum, order) => sum + Number(order.subtotal || 0), 0);
  const customerEmails = new Set(orders.map((order) => order.customer?.email).filter(Boolean));
  const productSales = new Map();

  orders.forEach((order) => {
    (order.items || []).forEach((item) => {
      productSales.set(item.name, (productSales.get(item.name) || 0) + Number(item.qty || 1));
    });
  });

  const topProducts = [...productSales.entries()]
    .sort((left, right) => right[1] - left[1])
    .slice(0, 5)
    .map(([name, sold]) => ({ name, sold }));

  return {
    total_orders: orders.length,
    total_revenue: totalRevenue,
    customers: customerEmails.size,
    top_products: topProducts,
  };
}

function buildStats(orders) {
  return {
    customers: Math.max(15000, 15000 + orders.length * 3),
    orders: Math.max(25000, 25000 + orders.length * 4),
    rating: 4.8,
  };
}

function formatWishlistItems(userId) {
  const ids = getWishlistDb(userId);
  return ids
    .map((productId) => findProductById(productId))
    .filter(Boolean)
    .map((product) => ({
      product_id: product.id,
      user_id: userId,
      created_at: nowIso(),
      product,
    }));
}

function parseJsonBody(options = {}) {
  if (options.body == null) {
    return null;
  }
  if (options.body instanceof FormData) {
    return options.body;
  }
  if (typeof options.body === "string") {
    try {
      return JSON.parse(options.body);
    } catch {
      return options.body;
    }
  }
  return options.body;
}

async function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(createHttpError(400, "Could not read the selected image."));
    reader.readAsDataURL(file);
  });
}

async function parseFormData(formData) {
  const parsed = {};
  for (const [key, value] of formData.entries()) {
    parsed[key] = value;
  }
  return parsed;
}

function normalizeProductPayload(input, existingProduct = null) {
  const name = String(input.name || "").trim();
  const category = String(input.category || "tshirt").trim().toLowerCase();
  const price = Number(input.price || 0);
  const sizes = String(input.sizes || existingProduct?.sizes?.join(", ") || "S, M, L, XL")
    .split(",")
    .map((size) => size.trim().toUpperCase())
    .filter(Boolean);
  const stock = Number(input.stock || 0);
  const featuredRaw = String(input.featured ?? existingProduct?.featured ?? false).toLowerCase();

  if (name.length < 3) {
    throw createHttpError(400, "Product name must be at least 3 characters.");
  }
  if (!["tshirt", "shirt"].includes(category)) {
    throw createHttpError(400, "Category must be tshirt or shirt.");
  }
  if (!Number.isFinite(price) || price <= 0) {
    throw createHttpError(400, "Price must be greater than zero.");
  }
  if (!Number.isFinite(stock) || stock < 0) {
    throw createHttpError(400, "Stock must be a valid number.");
  }

  return {
    name,
    category,
    price: Math.round(price),
    description: String(input.description || existingProduct?.description || "").trim(),
    tag: String(input.tag || existingProduct?.tag || "").trim(),
    sizes: sizes.length ? sizes : ["S", "M", "L", "XL"],
    stock: Math.round(stock),
    featured: ["true", "1", "yes", "on"].includes(featuredRaw),
    fit_type: existingProduct?.fit_type || (name.toLowerCase().includes("oversized") ? "Oversized Fit" : "Regular Fit"),
    neck_type: existingProduct?.neck_type || "Round Neck",
    material: existingProduct?.material || "Cotton",
    gsm: existingProduct?.gsm || 220,
    design_type: existingProduct?.design_type || "Plain",
    special_type: existingProduct?.special_type || "",
  };
}

async function buildProductImage(inputImage, existingImage) {
  if (!inputImage || typeof inputImage === "string") {
    return existingImage || "/images/hero-banner.png";
  }
  if (inputImage instanceof File && inputImage.size > 0) {
    return fileToDataUrl(inputImage);
  }
  return existingImage || "/images/hero-banner.png";
}

function shouldHandleLocally(url) {
  return (
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/products/") ||
    (url.pathname.endsWith("/products.html") && url.searchParams.get("format") === "json")
  );
}

async function handleStaticRequest(url, method, body, originalPath) {
  const pathname = url.pathname;

  if (pathname === "/api/products" && method === "GET") {
    const products = getProductsDb();
    return url.searchParams.get("featured") === "true" ? products.filter((product) => product.featured) : products;
  }

  const productMatch = pathname.match(/^\/api\/products\/(\d+)$/);
  if (productMatch && method === "GET") {
    const product = findProductById(Number(productMatch[1]));
    if (!product) {
      throw createHttpError(404, "Product not found.");
    }
    return product;
  }

  const fallbackProductMatch = pathname.match(/^\/products\/(\d+)$/);
  if (fallbackProductMatch && method === "GET") {
    const product = findProductById(Number(fallbackProductMatch[1]));
    if (!product) {
      throw createHttpError(404, "Product not found.");
    }
    return product;
  }

  if (pathname.endsWith("/products.html") && url.searchParams.get("format") === "json" && method === "GET") {
    return getProductsDb();
  }

  if (pathname === "/api/stats" && method === "GET") {
    return buildStats(getOrdersDb());
  }

  if (pathname === "/api/auth/me" && method === "GET") {
    const user = getAuthUser();
    return {
      authenticated: Boolean(user),
      user: user ? sanitizeUser(user) : null,
    };
  }

  if (pathname === "/api/auth/register" && method === "POST") {
    const users = getUsersDb();
    const name = String(body?.name || "").trim();
    const email = validateEmail(body?.email);
    const password = String(body?.password || "").trim();
    const confirmPassword = String(body?.confirm_password || "").trim();

    if (name.length < 2) {
      throw createHttpError(400, "Name must be at least 2 characters.");
    }
    if (password.length < 8) {
      throw createHttpError(400, "Password must be at least 8 characters.");
    }
    if (password !== confirmPassword) {
      throw createHttpError(400, "Passwords do not match.");
    }
    if (findUserByEmail(email)) {
      throw createHttpError(409, "An account with that email already exists.");
    }

    const currentYearSuffix = new Date().getFullYear().toString().slice(-2);
    let highestSeq = 0;
    const prefix = `TW${currentYearSuffix}-`;
    users.forEach(u => {
        if (u.user_id && u.user_id.startsWith(prefix)) {
            const seq = parseInt(u.user_id.split("-")[1], 10);
            if (!isNaN(seq) && seq > highestSeq) highestSeq = seq;
        }
    });
    
    const seqNumber = String(highestSeq + 1).padStart(3, "0");
    const userIdFormatted = `${prefix}${seqNumber}`;
    const otp = String(Math.floor(100000 + Math.random() * 900000));
    console.log(`[STATIC_BACKEND_MOCK] OTP for ${email} is: ${otp}`);

    const user = {
      id: nextNumericId(users),
      user_id: userIdFormatted,
      name,
      email,
      phone: "",
      password,
      role: "customer",
      otp: otp,
      otp_verification_status: false,
      profile_completed_status: false,
      created_at: nowIso(),
    };

    users.push(user);
    saveUsersDb(users);

    return {
      success: true,
      message: "Account created. Please check your email (or JS console) for the OTP.",
      email: email,
    };
  }

  if (pathname === "/api/auth/login" && method === "POST") {
    const user = findUserByEmail(body?.email);
    const inputPass = String(body?.password || "").trim();
    
    let isAuthValid = false;
    if (user && user.password && user.password === inputPass) isAuthValid = true;
    if (user && !user.password && user.password_hash) {
      if (inputPass === "admin123" || inputPass === "password") isAuthValid = true;
    }
    
    if (!isAuthValid) {
      throw createHttpError(401, "Incorrect email or password. (Hint: try 'admin123' or 'password' for seeded testing accounts)");
    }
    
    if (user.role !== "admin" && !user.otp_verification_status) {
      throw createHttpError(403, "Please verify your email OTP before logging in.");
    }

    return {
      success: true,
      token: createToken(user),
      user: { ...sanitizeUser(user), gender: user.gender, profile_completed_status: user.profile_completed_status },
    };
  }

  if (pathname === "/api/auth/otp/send" && method === "POST") {
    const phone = String(body?.phone || "").trim();
    if (!/^\d{10}$/.test(phone)) {
      throw createHttpError(400, "Please enter a valid 10-digit mobile number.");
    }
    return {
      success: true,
      message: "OTP sent successfully. Use 123456 for the static demo.",
    };
  }

  if (pathname === "/api/auth/otp/verify" && method === "POST") {
    const phone = String(body?.phone || "").trim();
    const otp = String(body?.otp || "").trim();
    if (otp !== "123456") {
      throw createHttpError(400, "Invalid OTP. Use 123456 for this static demo.");
    }

    const users = getUsersDb();
    let user = findUserByPhone(phone);
    if (!user) {
      user = {
        id: nextNumericId(users),
        name: body?.name ? String(body.name).trim() : `User ${phone.slice(-4)}`,
        email: `user${phone.slice(-4)}@trident.local`,
        phone,
        password: "123456",
        role: "customer",
        created_at: nowIso(),
      };
      users.push(user);
      saveUsersDb(users);
    }

    return {
      success: true,
      token: createToken(user),
      user: sanitizeUser(user),
    };
  }

  if (pathname === "/api/auth/otp/verify-email" && method === "POST") {
    const targetEmail = validateEmail(body?.email);
    const otp = String(body?.otp || "").trim();
    const users = getUsersDb();
    const userIndex = users.findIndex(u => u.email === targetEmail);
    
    if (userIndex === -1) throw createHttpError(404, "User not found.");
    const user = users[userIndex];
    if (user.otp_verification_status) throw createHttpError(400, "Account already verified.");
    if (user.otp !== otp) throw createHttpError(400, "Incorrect OTP.");
    
    user.otp_verification_status = true;
    users[userIndex] = user;
    saveUsersDb(users);
    
    return {
      success: true,
      message: "Email verified successfully.",
      user: sanitizeUser(user)
    };
  }

  if (pathname === "/api/auth/profile/setup" && method === "POST") {
    const userAuth = getAuthUser();
    if (!userAuth) throw createHttpError(401, "Unauthorized");
    
    const users = getUsersDb();
    const userIndex = users.findIndex(u => u.id === userAuth.id);
    if (userIndex !== -1) {
      users[userIndex].gender = body?.gender;
      if (body?.phone) users[userIndex].phone = body.phone;
      users[userIndex].profile_completed_status = true;
      saveUsersDb(users);
      return { success: true, message: "Profile setup complete", user: users[userIndex] };
    }
    throw createHttpError(404, "User not found.");
  }

  if (pathname === "/api/auth/google" && method === "POST") {
    const users = getUsersDb();
    const email = validateEmail(body?.email);
    let user = findUserByEmail(email);
    if (!user) {
      user = {
        id: nextNumericId(users),
        name: String(body?.name || "Google User").trim(),
        email,
        phone: "",
        password: "google-oauth",
        role: "customer",
        created_at: nowIso(),
      };
      users.push(user);
      saveUsersDb(users);
    }

    return {
      success: true,
      token: createToken(user),
      user: sanitizeUser(user),
    };
  }

  if (pathname === "/api/auth/logout" && method === "POST") {
    return { success: true, message: "Logged out." };
  }

  if (pathname === "/api/contact" && method === "POST") {
    const contacts = getContactsDb();
    const name = String(body?.name || "").trim();
    const email = validateEmail(body?.email);
    const message = String(body?.message || "").trim();

    if (name.length < 2) {
      throw createHttpError(400, "Name is required.");
    }
    if (message.length < 10) {
      throw createHttpError(400, "Message must be at least 10 characters.");
    }

    contacts.push({
      id: nextNumericId(contacts),
      name,
      email,
      message,
      created_at: nowIso(),
    });
    saveContactsDb(contacts);

    return { success: true, message: "Message sent successfully." };
  }

  const reviewsMatch = pathname.match(/^\/api\/reviews\/(\d+)$/);
  if (reviewsMatch && method === "GET") {
    return getReviewsDb().filter((review) => Number(review.product_id) === Number(reviewsMatch[1]));
  }

  if (pathname === "/api/reviews" && method === "POST") {
    const user = requireUser();
    const reviews = getReviewsDb();
    const productId = Number(body?.product_id);
    const rating = Number(body?.rating);
    const reviewText = String(body?.review || "").trim();

    if (!findProductById(productId)) {
      throw createHttpError(404, "Product not found.");
    }
    if (!Number.isFinite(rating) || rating < 1 || rating > 5) {
      throw createHttpError(400, "Rating must be between 1 and 5.");
    }
    if (reviews.some((review) => Number(review.user_id) === Number(user.id) && Number(review.product_id) === productId)) {
      throw createHttpError(400, "You have already reviewed this product.");
    }

    const review = {
      id: nextNumericId(reviews),
      user_id: user.id,
      user_name: user.name,
      product_id: productId,
      rating,
      review: reviewText,
      created_at: nowIso(),
    };
    reviews.push(review);
    saveReviewsDb(reviews);

    return { success: true, message: "Review submitted successfully.", review };
  }

  if (pathname === "/api/wishlist" && method === "GET") {
    const user = requireUser();
    return formatWishlistItems(user.id);
  }

  if (pathname === "/api/wishlist/add" && method === "POST") {
    const user = requireUser();
    const productId = Number(body?.product_id);
    if (!findProductById(productId)) {
      throw createHttpError(404, "Product not found.");
    }

    const wishlist = new Set(getWishlistDb(user.id));
    wishlist.add(productId);
    saveWishlistDb(user.id, [...wishlist]);

    return { success: true, message: "Added to wishlist." };
  }

  if (pathname === "/api/wishlist/remove" && ["DELETE", "POST"].includes(method)) {
    const user = requireUser();
    const productId = Number(body?.product_id);
    const wishlist = getWishlistDb(user.id).filter((id) => Number(id) !== productId);
    saveWishlistDb(user.id, wishlist);
    return { success: true, message: "Removed from wishlist." };
  }

  if (pathname === "/api/coupons/apply" && method === "POST") {
    const coupons = getCouponsDb();
    const code = String(body?.code || "").trim().toUpperCase();
    const subtotal = Number(body?.subtotal || 0);
    const coupon = coupons.find((entry) => entry.code === code);

    if (!coupon) {
      throw createHttpError(404, "Invalid coupon code.");
    }

    const discountAmount = roundCurrency((subtotal * Number(coupon.discount || 0)) / 100);
    return {
      code: coupon.code,
      discount_pct: coupon.discount,
      discount_amount: discountAmount,
      final_total: roundCurrency(subtotal - discountAmount),
    };
  }

  if (pathname === "/api/payment/create-order" && method === "POST") {
    return {
      key_id: "static_demo_checkout",
      razorpay_order_id: `order_${Math.random().toString(36).slice(2, 10)}`,
      amount: Number(body?.amount || 0),
      currency: body?.currency || "INR",
    };
  }

  if (pathname === "/api/payment/cod" && method === "POST") {
    const orderData = body || {};
    const orderResponse = createStaticOrder(orderData, "confirmed");
    return {
      success: true,
      message: "Order placed successfully.",
      order_id: orderResponse.order.order_id,
    };
  }

  if (pathname === "/api/payment/verify" && method === "POST") {
    const orderData = body?.order_data;
    if (!orderData) {
      throw createHttpError(400, "Missing order data.");
    }
    const orderResponse = createStaticOrder(orderData, "confirmed");
    return {
      success: true,
      message: "Payment verified successfully.",
      order_id: orderResponse.order.order_id,
    };
  }

  const trackingMatch = pathname.match(/^\/api\/orders\/([^/]+)\/tracking$/);
  if (trackingMatch && method === "GET") {
    const order = getOrdersDb().find((entry) => entry.order_id === trackingMatch[1]);
    return createTrackingPayload(order);
  }

  if (pathname === "/api/admin/orders" && method === "GET") {
    requireAdmin();
    return getOrdersDb();
  }

  const adminOrderMatch = pathname.match(/^\/api\/admin\/orders\/([^/]+)$/);
  if (adminOrderMatch && ["PATCH", "PUT"].includes(method)) {
    requireAdmin();
    const orders = getOrdersDb();
    const order = orders.find((entry) => entry.order_id === adminOrderMatch[1]);
    if (!order) {
      throw createHttpError(404, "Order not found.");
    }

    order.status = String(body?.status || order.status || "pending").toLowerCase();
    if (order.status === "shipped" && !order.tracking_id) {
      order.tracking_id = `SR${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
      order.courier = "Delhivery";
      order.estimated_delivery = new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    }

    saveOrdersDb(orders);
    return { success: true, message: "Order status updated.", order };
  }

  if (pathname === "/api/admin/analytics" && method === "GET") {
    requireAdmin();
    return buildAnalytics(getOrdersDb());
  }

  if (pathname === "/api/admin/products" && method === "POST") {
    requireAdmin();
    const products = getProductsDb();
    const parsed = body instanceof FormData ? await parseFormData(body) : body || {};
    const productData = normalizeProductPayload(parsed);
    const image = await buildProductImage(parsed.image, null);
    const product = {
      id: nextNumericId(products),
      ...productData,
      image: normalizeImagePath(image),
    };

    products.push(product);
    saveProductsDb(products);
    return { success: true, message: "Product added successfully.", product };
  }

  const adminProductMatch = pathname.match(/^\/api\/admin\/products\/(\d+)$/);
  if (adminProductMatch && method === "PUT") {
    requireAdmin();
    const productId = Number(adminProductMatch[1]);
    const products = getProductsDb();
    const index = products.findIndex((entry) => Number(entry.id) === productId);
    if (index === -1) {
      throw createHttpError(404, "Product not found.");
    }

    const parsed = body instanceof FormData ? await parseFormData(body) : body || {};
    const existing = products[index];
    const productData = normalizeProductPayload(parsed, existing);
    const image = await buildProductImage(parsed.image, existing.image);
    const updatedProduct = {
      ...existing,
      ...productData,
      image: normalizeImagePath(image),
    };

    products[index] = updatedProduct;
    saveProductsDb(products);
    return { success: true, message: "Product updated successfully.", product: updatedProduct };
  }

  if (adminProductMatch && method === "DELETE") {
    requireAdmin();
    const productId = Number(adminProductMatch[1]);
    const products = getProductsDb();
    const existing = products.find((entry) => Number(entry.id) === productId);
    if (!existing) {
      throw createHttpError(404, "Product not found.");
    }

    saveProductsDb(products.filter((entry) => Number(entry.id) !== productId));
    return { success: true, message: `${existing.name} deleted.` };
  }

  if (pathname === "/api/chat/send" && method === "POST") {
    const chat = getChatDb();
    const user = getAuthUser();
    const threadId = String(body?.thread_id || (user ? `user_${user.id}` : `anon_${Math.random().toString(36).slice(2, 10)}`));
    const author = user ? user.name : "Guest";

    const message = {
      id: nextNumericId(chat),
      thread_id: threadId,
      author,
      role: "user",
      message: String(body?.message || "").trim(),
      timestamp: nowIso(),
      read: false,
    };

    chat.push(message);
    chat.push({
      id: nextNumericId(chat),
      thread_id: threadId,
      author: "Supporting Staff",
      role: "admin",
      message: "We have received your message. Our team will review it shortly. For faster help, use the WhatsApp link below.",
      timestamp: new Date(Date.now() + 1000).toISOString(),
      read: true,
    });
    saveChatDb(chat);

    return {
      success: true,
      message,
      thread_id: threadId,
    };
  }

  if (pathname === "/api/chat/messages" && method === "GET") {
    const threadId = url.searchParams.get("thread_id");
    if (!threadId) {
      return [];
    }
    return getChatDb().filter((entry) => entry.thread_id === threadId);
  }

  throw createHttpError(404, `Mock route not found for ${originalPath}`);
}

function createStaticOrder(orderData, defaultStatus) {
  const orders = getOrdersDb();
  const user = getAuthUser();
  const items = Array.isArray(orderData?.items) ? orderData.items : [];
  if (!items.length) {
    throw createHttpError(400, "Your cart is empty.");
  }

  const customerName = String(orderData?.customer?.name || "").trim();
  const customerEmail = validateEmail(orderData?.customer?.email || `${customerName || "guest"}@example.com`);
  const customerPhone = String(orderData?.customer?.phone || "").trim();
  const address = String(orderData?.shipping?.address || "").trim();
  const city = String(orderData?.shipping?.city || "").trim();

  if (customerName.length < 2) {
    throw createHttpError(400, "Customer name is required.");
  }
  if (address.length < 6 || city.length < 2) {
    throw createHttpError(400, "Complete shipping details are required.");
  }
  if (customerPhone.length < 8) {
    throw createHttpError(400, "A valid phone number is required.");
  }

  const order = {
    order_id: createOrderId(),
    items: items.map((item) => ({
      id: Number(item.id),
      name: String(item.name || ""),
      price: Number(item.price || 0),
      image: normalizeImagePath(item.image),
      qty: Math.max(1, Number(item.qty || 1)),
      size: String(item.size || "M"),
    })),
    subtotal: Math.round(Number(orderData?.subtotal || 0)),
    customer: {
      name: customerName,
      email: customerEmail,
      phone: customerPhone,
      user_id: user?.id || null,
    },
    shipping: {
      address,
      city,
      postal_code: String(orderData?.shipping?.postal_code || "").trim(),
      country: String(orderData?.shipping?.country || "India").trim() || "India",
      notes: String(orderData?.shipping?.notes || "").trim(),
    },
    status: defaultStatus,
    created_at: nowIso(),
  };

  orders.unshift(order);
  saveOrdersDb(orders);

  return { order };
}

export function resolveUrl(path) {
  if (/^(https?:)?\/\//.test(path) || String(path).startsWith("data:")) {
    return path;
  }
  const cleanPath = String(path || "").replace(/^\.\//, "").replace(/^\//, "");
  return new URL(cleanPath, SITE_ROOT).href;
}

export function resolveAssetUrl(path) {
  if (!path) {
    return resolveUrl("images/hero-banner.png");
  }
  return resolveUrl(path);
}

export function getAuthSession() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return memoryStore.get(AUTH_STORAGE_KEY) || null;
  }
}

export function saveAuthSession(session) {
  try {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
  } catch {
    memoryStore.set(AUTH_STORAGE_KEY, session);
  }
  return session;
}

export function clearAuthSession() {
  removeStorage(AUTH_STORAGE_KEY);
}

export async function request(path, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  const url = new URL(resolveUrl(path));
  const body = parseJsonBody(options);

  try {
    if (shouldHandleLocally(url)) {
      return await handleStaticRequest(url, method, body, path);
    }

    const response = await fetch(resolveUrl(path), options);
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : null;
    if (!response.ok) {
      throw createHttpError(response.status, payload?.detail || payload?.message || "Request failed.");
    }
    return payload;
  } catch (error) {
    if (error instanceof Error) {
      error.path = path;
      if (!("status" in error)) {
        error.status = 500;
      }
    }
    throw error;
  }
}

export async function requestWithFallback(paths, options = {}) {
  let lastError = null;

  for (const path of paths) {
    try {
      return await request(path, options);
    } catch (error) {
      lastError = error;
      if (error.status !== 404) {
        throw error;
      }
    }
  }

  throw lastError || createHttpError(500, "Request failed.");
}

export function get(path) {
  return request(path);
}

export function getWithFallback(paths) {
  return requestWithFallback(paths);
}

export function post(path, body) {
  return request(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export function postWithFallback(paths, body) {
  return requestWithFallback(paths, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export function del(path) {
  return request(path, {
    method: "DELETE",
  });
}

export function postForm(path, formData) {
  return request(path, {
    method: "POST",
    body: formData,
  });
}

export function putForm(path, formData) {
  return request(path, {
    method: "PUT",
    body: formData,
  });
}
