import { initSite, getCurrentUser } from "../shared/site.js";

async function loadProfile() {
  await initSite();
  const user = getCurrentUser();

  if (!user) {
    // If not logged in, redirect to login
    window.location.href = "login.html";
    return;
  }

  const nameEl = document.getElementById("profile-name");
  const emailEl = document.getElementById("profile-email");
  const roleEl = document.getElementById("profile-role");

  if (nameEl) nameEl.textContent = user.name || "N/A";
  if (emailEl) emailEl.textContent = user.email || "N/A";
  if (roleEl) roleEl.textContent = user.role === "admin" ? "Administrator" : "Customer";
}

loadProfile();
