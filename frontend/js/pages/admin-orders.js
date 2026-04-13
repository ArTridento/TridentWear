import { get, request } from "../shared/api.js";
import { formatCurrency, initSite, showToast } from "../shared/site.js";

let allOrders = [];

function statusBadge(s) {
  const label = s || "pending";
  return `<span class="status-badge ${label}">${label}</span>`;
}

function itemsSummary(items = []) {
  if (!items.length) return "—";
  const top = items[0];
  const more = items.length > 1 ? ` +${items.length - 1} more` : "";
  return `${top.name} ×${top.qty}${more}`;
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function renderTable(orders) {
  const tbody = document.querySelector("[data-orders-body]");
  if (!orders.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--gray);">No orders found.</td></tr>`;
    return;
  }

  tbody.innerHTML = orders.map(o => `
    <tr data-order-row="${o.order_id}">
      <td><code style="font-size:0.8rem;color:var(--primary);">${o.order_id}</code></td>
      <td>
        <div style="font-weight:600;color:var(--gray-dark);">${o.customer?.name || "—"}</div>
        <div style="font-size:0.78rem;color:var(--gray);">${o.customer?.email || ""}</div>
      </td>
      <td style="max-width:14rem;">${itemsSummary(o.items)}</td>
      <td><strong style="color:var(--secondary);">${formatCurrency(o.subtotal || 0)}</strong></td>
      <td style="white-space:nowrap;">${fmtDate(o.created_at)}</td>
      <td>${statusBadge(o.status)}</td>
      <td>
        <select class="status-select" data-status-select="${o.order_id}" title="Change status">
          <option value="pending"   ${o.status === "pending"   ? "selected" : ""}>Pending</option>
          <option value="confirmed" ${o.status === "confirmed" ? "selected" : ""}>Confirmed</option>
          <option value="shipped"   ${o.status === "shipped"   ? "selected" : ""}>Shipped</option>
          <option value="delivered" ${o.status === "delivered" ? "selected" : ""}>Delivered</option>
        </select>
      </td>
    </tr>
  `).join("");

  // Bind selects
  tbody.querySelectorAll("[data-status-select]").forEach(sel => {
    sel.addEventListener("change", async () => {
      const orderId = sel.dataset.statusSelect;
      const newStatus = sel.value;
      try {
        await request(`/api/admin/orders/${orderId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: newStatus }),
        });
        // Update local array
        const order = allOrders.find(o => o.order_id === orderId);
        if (order) order.status = newStatus;
        // Update badge in same row
        const row = document.querySelector(`[data-order-row="${orderId}"]`);
        if (row) row.querySelector(".status-badge").outerHTML = statusBadge(newStatus);
        // Re-insert badge (outerHTML replacement doesn't work on td node directly, re-render badge cell)
        const cells = row.querySelectorAll("td");
        cells[5].innerHTML = statusBadge(newStatus);
        updateStats(allOrders);
        showToast(`Order ${orderId} marked as ${newStatus}.`);
      } catch (err) {
        showToast(err.message, "error");
        // Revert
        const order = allOrders.find(o => o.order_id === orderId);
        if (order) sel.value = order.status;
      }
    });
  });
}

function updateStats(orders) {
  document.querySelector("[data-stat-total]").textContent = orders.length;
  document.querySelector("[data-stat-pending]").textContent =
    orders.filter(o => !o.status || o.status === "pending").length;
  document.querySelector("[data-stat-delivered]").textContent =
    orders.filter(o => o.status === "delivered").length;
}

function applyFilters() {
  const statusFilter = document.getElementById("filter-status").value;
  const searchFilter = document.getElementById("filter-search").value.toLowerCase().trim();

  let filtered = allOrders;
  if (statusFilter) filtered = filtered.filter(o => o.status === statusFilter);
  if (searchFilter) {
    filtered = filtered.filter(o =>
      (o.order_id || "").toLowerCase().includes(searchFilter) ||
      (o.customer?.name || "").toLowerCase().includes(searchFilter) ||
      (o.customer?.email || "").toLowerCase().includes(searchFilter)
    );
  }
  renderTable(filtered);
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();

  try {
    allOrders = (await get("/api/admin/orders")) || [];
    // Sort newest first
    allOrders.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    updateStats(allOrders);
    renderTable(allOrders);
  } catch (err) {
    document.querySelector("[data-orders-body]").innerHTML =
      `<tr><td colspan="7" style="text-align:center;padding:2rem;color:var(--danger);">${err.message}</td></tr>`;
  }

  document.getElementById("filter-status").addEventListener("change", applyFilters);
  document.getElementById("filter-search").addEventListener("input", applyFilters);
});
