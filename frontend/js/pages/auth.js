import { post, saveAuthSession } from "../shared/api.js";
import { getCurrentUser, initSite, refreshAuthState, showToast } from "../shared/site.js";

function setActiveTab(target) {
  document.querySelectorAll("[data-auth-tab]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.authTab === target);
  });
  document.querySelectorAll("[data-auth-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.authPanel !== target;
  });
}

function nextPath() {
  const params = new URLSearchParams(window.location.search);
  return params.get("next") || "";
}

function redirectAfterAuth(user) {
  const next = nextPath();
  if (next) {
    window.location.href = next;
    return;
  }
  window.location.href = user.role === "admin" ? "/admin" : "/products";
}

function updateStatus() {
  const user = getCurrentUser();
  const status = document.querySelector("[data-auth-status]");

  if (!user) {
    status.hidden = true;
    return;
  }

  status.hidden = false;
  status.innerHTML = `
    <div class="helper-note success">
      <strong>${user.name}</strong>
      <span>Signed in as ${user.email}</span>
    </div>
  `;
}

function bindTabs() {
  document.querySelectorAll("[data-auth-tab]").forEach((button) => {
    button.addEventListener("click", () => setActiveTab(button.dataset.authTab));
  });
}

function bindRegister() {
  const form = document.querySelector("[data-register-form]");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      const data = await post("/api/auth/register", {
        name: form.querySelector("#register-name").value.trim(),
        email: form.querySelector("#register-email").value.trim(),
        password: form.querySelector("#register-password").value.trim(),
      });
      saveAuthSession({ token: data.token, user: data.user });
      await refreshAuthState();
      updateStatus();
      showToast("Account created successfully.");
      redirectAfterAuth(data.user);
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

function bindLogin() {
  const form = document.querySelector("[data-login-form]");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      const data = await post("/api/auth/login", {
        email: form.querySelector("#login-email").value.trim(),
        password: form.querySelector("#login-password").value.trim(),
      });
      saveAuthSession({ token: data.token, user: data.user });
      await refreshAuthState();
      updateStatus();
      showToast("Welcome back.");
      redirectAfterAuth(data.user);
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  updateStatus();
  bindTabs();
  bindRegister();
  bindLogin();
  setActiveTab(nextPath() ? "login" : "register");
});
