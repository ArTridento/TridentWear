import { post, saveAuthSession } from "../shared/api.js";
import { escapeHtml, getCurrentUser, initSite, refreshAuthState, showToast } from "../shared/site.js";

function nextPath() {
  const params = new URLSearchParams(window.location.search);
  return params.get("next") || "";
}

function buildPath(path) {
  const next = nextPath();
  return next ? `${path}?next=${encodeURIComponent(next)}` : path;
}

function redirectAfterAuth(user) {
  const next = nextPath();
  if (next) {
    window.location.href = next;
    return;
  }

  window.location.href = user.role === "admin" ? "/admin" : "/products";
}

function renderAuthStatus() {
  const user = getCurrentUser();
  const status = document.querySelector("[data-auth-status]");
  if (!status) {
    return;
  }

  if (!user) {
    status.hidden = true;
    status.innerHTML = "";
    return;
  }

  status.hidden = false;
  status.innerHTML = `
    <div class="auth-status-card">
      <strong>Hello, ${escapeHtml(user.name.split(" ")[0] || user.name)}</strong>
      <span>Signed in as ${escapeHtml(user.email)}</span>
    </div>
  `;
}

function wireSwitchLinks(mode) {
  const alternatePath = mode === "login" ? "/register" : "/login";
  document.querySelectorAll("[data-auth-switch]").forEach((link) => {
    link.setAttribute("href", buildPath(alternatePath));
  });
}

function setSubmitting(form, isSubmitting, idleLabel, pendingLabel) {
  const button = form.querySelector("button[type='submit']");
  if (!button) {
    return;
  }

  button.disabled = isSubmitting;
  button.textContent = isSubmitting ? pendingLabel : idleLabel;
}

function bindRegisterForm() {
  const form = document.querySelector("[data-register-form]");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const name = form.querySelector("#register-name")?.value.trim() || "";
    const email = form.querySelector("#register-email")?.value.trim() || "";
    const password = form.querySelector("#register-password")?.value.trim() || "";
    const confirmPassword = form.querySelector("#register-confirm-password")?.value.trim() || "";

    if (!name || !email || !password || !confirmPassword) {
      showToast("Please complete every registration field.", "error");
      return;
    }

    if (password !== confirmPassword) {
      showToast("Passwords do not match.", "error");
      return;
    }

    setSubmitting(form, true, "Create Account", "Creating Account...");
    try {
      const data = await post("/register", {
        name,
        email,
        password,
        confirm_password: confirmPassword,
      });

      saveAuthSession({ token: data.token, user: data.user });
      await refreshAuthState();
      renderAuthStatus();
      redirectAfterAuth(data.user);
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      setSubmitting(form, false, "Create Account", "Creating Account...");
    }
  });
}

function bindLoginForm() {
  const form = document.querySelector("[data-login-form]");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = form.querySelector("#login-email")?.value.trim() || "";
    const password = form.querySelector("#login-password")?.value.trim() || "";

    if (!email || !password) {
      showToast("Enter your email and password.", "error");
      return;
    }

    setSubmitting(form, true, "Login", "Signing In...");
    try {
      const data = await post("/login", { email, password });
      saveAuthSession({ token: data.token, user: data.user });
      await refreshAuthState();
      renderAuthStatus();
      redirectAfterAuth(data.user);
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      setSubmitting(form, false, "Login", "Signing In...");
    }
  });
}

export async function initAuthPage(mode) {
  await initSite();
  wireSwitchLinks(mode);
  renderAuthStatus();
  bindRegisterForm();
  bindLoginForm();
}
