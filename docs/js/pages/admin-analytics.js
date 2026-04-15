import { get } from "../shared/api.js";
import { formatCurrency, initSite } from "../shared/site.js";

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}

function statusBadge(s) {
  const label = s || "pending";
  return `<span class="status-badge ${label}">${label}</span>`;
}

function animateCount(el, target, prefix = "", suffix = "", duration = 900) {
  const start = performance.now();
  const isFloat = !Number.isInteger(target);
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    const ease = p * (2 - p);
    const val = isFloat ? (ease * target).toFixed(1) : Math.floor(ease * target);
    el.textContent = prefix + val.toLocaleString("en-IN") + suffix;
    if (p < 1) requestAnimationFrame(step);
    else el.textContent = prefix + target.toLocaleString("en-IN") + suffix;
  }
  requestAnimationFrame(step);
}

function renderBarChart(topProducts) {
  const container = document.querySelector("[data-bar-chart]");
  if (!topProducts.length) {
    container.innerHTML = `<div style="color:var(--gray);font-size:0.88rem;align-self:center;">No sales data yet.</div>`;
    return;
  }

  const max = Math.max(...topProducts.map(p => p.sold));
  container.innerHTML = topProducts.map(p => `
    <div class="bar-item">
      <div class="bar-value">${p.sold}</div>
      <div class="bar-fill" style="height:${Math.round((p.sold / max) * 100)}%;" title="${p.name}: ${p.sold} sold"></div>
      <div class="bar-label">${p.name.length > 14 ? p.name.slice(0, 13) + "…" : p.name}</div>
    </div>
  `).join("");
}

function renderRevenueBreakdown(topProducts, totalRevenue) {
  const container = document.querySelector("[data-revenue-breakdown]");
  if (!topProducts.length) {
    container.innerHTML = `<p style="color:var(--gray);font-size:0.88rem;">No data yet.</p>`;
    return;
  }

  const totalUnits = topProducts.reduce((s, p) => s + p.sold, 0);
  container.innerHTML = topProducts.map(p => {
    const pct = totalUnits ? Math.round((p.sold / totalUnits) * 100) : 0;
    return `
      <div>
        <div style="display:flex;justify-content:space-between;font-size:0.82rem;margin-bottom:0.25rem;">
          <span style="color:var(--gray-dark);font-weight:600;">${p.name}</span>
          <span style="color:var(--gray);">${pct}% of units</span>
        </div>
        <div style="height:6px;background:#e9ecef;border-radius:999px;overflow:hidden;">
          <div style="height:100%;width:${pct}%;background:var(--primary);border-radius:999px;transition:width 0.6s ease;"></div>
        </div>
      </div>
    `;
  }).join("");
}

function renderRecentOrders(orders) {
  const tbody = document.querySelector("[data-recent-orders]");
  const recent = orders.slice(0, 8);

  if (!recent.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:1.5rem;color:var(--gray);">No orders yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = recent.map(o => `
    <tr>
      <td><code style="font-size:0.8rem;color:var(--primary);">${o.order_id}</code></td>
      <td style="font-weight:600;color:var(--gray-dark);">${o.customer?.name || "—"}</td>
      <td><strong style="color:var(--secondary);">${formatCurrency(o.subtotal || 0)}</strong></td>
      <td>${statusBadge(o.status)}</td>
      <td style="white-space:nowrap;">${fmtDate(o.created_at)}</td>
    </tr>
  `).join("");
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();

  try {
    const data = await get("/api/admin/analytics");

    // KPI cards
    animateCount(document.querySelector("[data-kpi-orders]"), data.total_orders);
    animateCount(document.querySelector("[data-kpi-revenue]"), data.total_revenue, "₹");
    animateCount(document.querySelector("[data-kpi-customers]"), data.customers);

    // Charts
    renderBarChart(data.top_products || []);
    renderRevenueBreakdown(data.top_products || [], data.total_revenue);

    // Recent orders (fetch from orders endpoint)
    try {
      const ordersData = await get("/api/admin/orders");
      const sorted = (ordersData || []).sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      renderRecentOrders(sorted);
    } catch (_) {
      document.querySelector("[data-recent-orders]").innerHTML =
        `<tr><td colspan="5" style="text-align:center;padding:1.5rem;color:var(--gray);">Could not load orders.</td></tr>`;
    }

  } catch (err) {
    document.querySelector("[data-kpi-orders]").textContent = "—";
    document.querySelector("[data-kpi-revenue]").textContent = "—";
    document.querySelector("[data-kpi-customers]").textContent = "—";
    document.querySelector("[data-bar-chart]").innerHTML =
      `<div style="color:var(--danger);font-size:0.88rem;align-self:center;">${err.message}</div>`;
  }
});
