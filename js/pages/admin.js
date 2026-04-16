import { del, get, postForm, putForm, resolveAssetUrl } from "../shared/api.js";
import { normalizeProduct } from "../shared/catalog.js";
import { createLoaderMarkup, formatCurrency, getCurrentUser, initSite, showToast } from "../shared/site.js";

let products = [];
let editingProductId = null;

function fields() {
  return {
    name: document.querySelector("#admin-name"),
    category: document.querySelector("#admin-category"),
    price: document.querySelector("#admin-price"),
    description: document.querySelector("#admin-description"),
    tag: document.querySelector("#admin-tag"),
    sizes: document.querySelector("#admin-sizes"),
    stock: document.querySelector("#admin-stock"),
    featured: document.querySelector("#admin-featured"),
    image: document.querySelector("#admin-image"),
  };
}

function setFormState(product = null) {
  const f = fields();
  const title = document.querySelector("[data-admin-form-title]");
  const submit = document.querySelector("[data-admin-submit]");
  const cancel = document.querySelector("[data-admin-cancel]");
  const preview = document.querySelector("[data-preview-image]");

  if (!product) {
    editingProductId = null;
    title.textContent = "Add New Product";
    submit.textContent = "Save Product";
    cancel.hidden = true;
    f.name.value = "";
    f.category.value = "tshirt";
    f.price.value = "";
    f.description.value = "";
    f.tag.value = "";
    f.sizes.value = "S, M, L, XL";
    f.stock.value = "100";
    f.featured.checked = false;
    f.image.value = "";
    preview.hidden = true;
    preview.src = "";
    return;
  }

  editingProductId = product.id;
  title.textContent = `Edit ${product.name}`;
  submit.textContent = "Update Product";
  cancel.hidden = false;
  f.name.value = product.name;
  f.category.value = product.category;
  f.price.value = product.price;
  f.description.value = product.description;
  f.tag.value = product.tag || "";
  f.sizes.value = product.sizes.join(", ");
  f.stock.value = product.stock;
  f.featured.checked = Boolean(product.featured);
  f.image.value = "";
  preview.hidden = false;
    preview.src = resolveAssetUrl(product.image);
}

function bindPreview() {
  const input = document.querySelector("#admin-image");
  const preview = document.querySelector("[data-preview-image]");

  input.addEventListener("change", () => {
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    preview.hidden = false;
    preview.src = URL.createObjectURL(file);
  });
}

function renderSummary() {
  document.querySelector("[data-summary-total]").textContent = String(products.length);
  document.querySelector("[data-summary-shirts]").textContent = String(products.length);
  document.querySelector("[data-summary-featured]").textContent = String(products.filter((product) => product.featured).length);
}

function renderProducts() {
  const list = document.querySelector("[data-admin-product-list]");
  if (!products.length) {
    list.innerHTML = `<div class="helper-note warning">No products found yet. Use the form to add the first drop.</div>`;
    return;
  }

  list.innerHTML = products
    .map(
      (product) => `
        <article class="admin-product-card">
          <div class="admin-product-top">
            <div>
              <strong>${product.name}</strong>
              <div class="section-copy">T-Shirt - ${formatCurrency(product.price)}</div>
              <div class="section-copy">${product.card_tags.join(" / ")}</div>
              <div class="section-copy">${product.stock} stock - ${product.featured ? "Featured" : "Standard"}</div>
            </div>
            <img class="admin-thumb" src="${resolveAssetUrl(product.image)}" alt="${product.name}">
          </div>
          <p class="section-copy">${product.description}</p>
          <div class="admin-actions">
            <button class="btn btn-outline" type="button" data-edit-product="${product.id}">Edit</button>
            <button class="btn btn-danger" type="button" data-delete-product="${product.id}">Delete</button>
          </div>
        </article>
      `,
    )
    .join("");

  list.querySelectorAll("[data-edit-product]").forEach((button) => {
    button.addEventListener("click", () => {
      const product = products.find((entry) => entry.id === Number(button.dataset.editProduct));
      if (product) {
        setFormState(product);
      }
    });
  });

  list.querySelectorAll("[data-delete-product]").forEach((button) => {
    button.addEventListener("click", async () => {
      const product = products.find((entry) => entry.id === Number(button.dataset.deleteProduct));
      if (!product || !window.confirm(`Delete ${product.name}?`)) {
        return;
      }

      try {
        await del(`/api/admin/products/${product.id}`);
        showToast(`${product.name} deleted.`);
        await loadProducts();
      } catch (error) {
        showToast(error.message, "error");
      }
    });
  });
}

async function loadProducts() {
  const list = document.querySelector("[data-admin-product-list]");
  list.innerHTML = createLoaderMarkup("Loading product manager...");
  const data = await get("/api/products");
  products = (Array.isArray(data) ? data : data.products || []).map(normalizeProduct);
  renderSummary();
  renderProducts();
}

function buildFormData() {
  const f = fields();
  const formData = new FormData();
  formData.append("name", f.name.value.trim());
  formData.append("category", f.category.value);
  formData.append("price", f.price.value.trim());
  formData.append("description", f.description.value.trim());
  formData.append("tag", f.tag.value.trim());
  formData.append("sizes", f.sizes.value.trim());
  formData.append("stock", f.stock.value.trim());
  formData.append("featured", f.featured.checked ? "true" : "false");
  if (f.image.files?.[0]) {
    formData.append("image", f.image.files[0]);
  }
  return formData;
}

function bindForm() {
  const form = document.querySelector("[data-admin-form]");
  const cancel = document.querySelector("[data-admin-cancel]");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = document.querySelector("[data-admin-submit]");
    submit.disabled = true;
    submit.textContent = editingProductId ? "Updating..." : "Saving...";

    try {
      if (editingProductId) {
        await putForm(`/api/admin/products/${editingProductId}`, buildFormData());
        showToast("Product updated.");
      } else {
        await postForm("/api/admin/products", buildFormData());
        showToast("Product created.");
      }
      setFormState();
      await loadProducts();
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      submit.disabled = false;
      submit.textContent = editingProductId ? "Update Product" : "Save Product";
    }
  });

  cancel.addEventListener("click", () => setFormState());
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  const user = getCurrentUser();
  if (!user || user.role !== "admin") {
    window.location.href = "login.html?next=admin.html";
    return;
  }

  bindForm();
  bindPreview();
  setFormState();

  try {
    await loadProducts();
  } catch (error) {
    document.querySelector("[data-admin-product-list]").innerHTML = `<div class="helper-note danger">${error.message}</div>`;
  }
});
