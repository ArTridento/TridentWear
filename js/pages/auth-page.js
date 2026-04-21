import { post, saveAuthSession } from "../shared/api.js?v=8";
import { escapeHtml, getCurrentUser, initSite, refreshAuthState, showToast } from "../shared/site.js?v=8";

function nextPath() {
  const params = new URLSearchParams(window.location.search);
  return normalizeNextPath(params.get("next") || "");
}

function normalizeNextPath(path) {
  const raw = String(path || "").trim();
  if (!raw) {
    return "";
  }

  const normalized = raw.startsWith("/") ? raw.slice(1) : raw;
  const routeMap = {
    "": "index.html",
    admin: "admin.html",
    wishlist: "wishlist.html",
    login: "login.html",
    register: "register.html",
    products: "products.html",
    product: "product.html",
    cart: "cart.html",
    checkout: "checkout.html",
    about: "about.html",
    contact: "contact.html",
    privacy: "privacy.html",
    terms: "terms.html",
    returns: "returns.html",
    shipping: "shipping.html",
    track: "track.html",
  };

  return routeMap[normalized] || normalized;
}

function buildPath(path) {
  const next = nextPath();
  return next ? `${path}?next=${encodeURIComponent(next)}` : path;
}

function redirectAfterAuth(user) {
  if (user && user.profile_completed_status === false) {
    window.location.href = `profile-setup.html`;
    return;
  }
  
  const next = nextPath();
  if (next) {
    window.location.href = next;
    return;
  }

  window.location.href = user.role === "admin" ? "admin.html" : "profile.html";
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
      <span>Signed in as ${escapeHtml(user.email || user.phone)}</span>
    </div>
  `;
}

function wireSwitchLinks(mode) {
  const alternatePath = mode === "login" ? "register.html" : "login.html";
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

      // Show dev OTP if present
      if (data.dev_otp) {
        showToast(data.message.replace(data.dev_otp, '***') + "\nDev OTP: " + data.dev_otp, "success");
      } else {
        showToast(data.message || "Please check your email for OTP.", "success");
      }
      setTimeout(() => {
        window.location.href = `verify.html?email=${encodeURIComponent(email)}`;
      }, 3000); // give them time to read the OTP
    } catch (error) {
      showToast(error.message, "error");
    } finally {
      setSubmitting(form, false, "Create Account", "Creating Account...");
    }
  });
}

function bindOtpLogin() {
  const sendOtpBtn = document.getElementById("send-otp-btn");
  const mobileInput = document.getElementById("login-mobile");
  const otpContainer = document.getElementById("otp-field-container");
  const otpInput = document.getElementById("login-otp");

  if (!sendOtpBtn) return;

  sendOtpBtn.addEventListener("click", async () => {
    const mobile = mobileInput.value.trim();
    if (!mobile || !/^[0-9]{10}$/.test(mobile)) {
      showToast("Please enter a valid 10-digit mobile number.", "error");
      return;
    }

    if (otpContainer.style.display === "none") {
      sendOtpBtn.disabled = true;
      sendOtpBtn.textContent = "Sending...";
      
      try {
        const data = await post("/api/auth/otp/send", { phone: mobile });
        otpContainer.style.display = "block";
        sendOtpBtn.textContent = "Verify & Login";
        sendOtpBtn.classList.replace("btn-secondary", "btn-primary");
        if (data.dev_otp) {
           showToast("OTP sent to your mobile!\nDev OTP: " + data.dev_otp, "success");
        } else {
           showToast("OTP sent to your mobile!", "success");
        }
      } catch (err) {
        showToast(err.message, "error");
        sendOtpBtn.textContent = "Send OTP";
      } finally {
        sendOtpBtn.disabled = false;
      }
    } else {
      const otp = otpInput.value.trim();
      if (!otp || otp.length < 6) {
        showToast("Please enter the 6-digit OTP.", "error");
        return;
      }

      sendOtpBtn.disabled = true;
      sendOtpBtn.textContent = "Verifying...";

      try {
        const data = await post("/api/auth/otp/verify", { phone: mobile, otp });
        showToast("Login successful!", "success");
        saveAuthSession({ token: data.token, user: data.user });
        await refreshAuthState();
        redirectAfterAuth(data.user);
      } catch (err) {
        showToast(err.message, "error");
        sendOtpBtn.textContent = "Verify & Login";
      } finally {
        sendOtpBtn.disabled = false;
      }
    }
  });
}

window.handleGoogleCredentialResponse = async (response) => {
  if (!response || !response.credential) return;
  
  showToast("Verifying with Google...", "info");
  try {
    const data = await post("/api/auth/google", { credential: response.credential });
    saveAuthSession({ token: data.token, user: data.user });
    await refreshAuthState();
    showToast("Signed in with Google!", "success");
    redirectAfterAuth(data.user);
  } catch (err) {
    showToast(err.message, "error");
  }
};

function bindForgotPassword() {
  const link = document.getElementById("forgot-password-link");
  if (!link) return;
  link.addEventListener("click", async (e) => {
    e.preventDefault();
    const email = prompt("Enter your email address to reset password:");
    if (!email) return;

    try {
      showToast("Requesting password reset...", "info");
      const res = await post("/api/auth/password/forgot", { email });
      if (res.dev_otp) {
         showToast(res.message, "success");
         const otp = prompt(`Dev Mode: We displayed the OTP in the message.\nEnter the 6-digit OTP you received:\n(Hint: It's ${res.dev_otp})`);
         if (!otp) return;
         const newPass = prompt("Enter your new password (min 8 chars):");
         if (!newPass) return;
         
         const resetRes = await post("/api/auth/password/reset", { email, otp, new_password: newPass });
         showToast(resetRes.message, "success");
      } else {
         // In dev mode, if dev_otp is missing, it means the email was not found.
         showToast("Dev Mode: No dev_otp received. The email might not be registered or you made a typo. Check db/users.json.", "warning");
         const otp = prompt("Dev Mode Error: No OTP returned.\nEnter the 6-digit OTP sent to your email:");
         if (!otp) return;
         const newPass = prompt("Enter your new password (min 8 chars):");
         if (!newPass) return;
         
         const resetRes = await post("/api/auth/password/reset", { email, otp, new_password: newPass });
         showToast(resetRes.message, "success");
      }
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

function bindLoginForm() {
  const form = document.querySelector("[data-login-form]");
  if (!form) return;

  form.addEventListener("submit", async (event) => {
    const emailBlock = document.getElementById("email-login-block");
    if (emailBlock && emailBlock.style.display === "none") {
      event.preventDefault();
      return;
    }

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
  if (mode === "login") {
    bindOtpLogin();
    bindForgotPassword();
  }
}
