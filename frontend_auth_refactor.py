import os
import glob
import re

html_dir = r"d:\TridentWear\frontend\html"
js_dir = r"d:\TridentWear\frontend\js\pages"
shared_dir = r"d:\TridentWear\frontend\js\shared"

with open(os.path.join(html_dir, "auth.html"), "r", encoding="utf-8") as f:
    auth_html = f.read()

# 1. Create login.html
login_html = auth_html.replace(
    '<body data-page="auth">', '<body data-page="login">'
).replace(
    '<script type="module" src="../js/pages/auth.js"></script>',
    '<script type="module" src="../js/pages/login.js"></script>'
)

login_html = re.sub(
    r'<section data-auth-panel="register">.*?</section>',
    '',
    login_html,
    flags=re.DOTALL
)
login_html = login_html.replace('<section data-auth-panel="login" hidden>', '<section data-auth-panel="login">')
login_html = login_html.replace('<button class="tab-button is-active" type="button" data-auth-tab="register">Register</button>', '<a class="tab-button" href="/register">Register</a>')
login_html = login_html.replace('<button class="tab-button" type="button" data-auth-tab="login">Login</button>', '<a class="tab-button is-active" href="/login">Login</a>')
login_html = login_html.replace('data-auth-status hidden', 'data-auth-status hidden') # keep it
login_html = login_html.replace('<title>Login / Register | TridentWear</title>', '<title>Login | TridentWear</title>')
login_html = login_html.replace('<p class="auth-display-copy">\n            Register to save your details for checkout, or sign in to manage the store if you are the local admin.\n          </p>', '<p class="auth-display-copy">\n            Sign in to your account or manage the store if you are the local admin.\n          </p>')


# 2. Create register.html
register_html = auth_html.replace(
    '<body data-page="auth">', '<body data-page="register">'
).replace(
    '<script type="module" src="../js/pages/auth.js"></script>',
    '<script type="module" src="../js/pages/register.js"></script>'
)

register_html = re.sub(
    r'<section data-auth-panel="login" hidden>.*?</section>',
    '',
    register_html,
    flags=re.DOTALL
)
register_html = register_html.replace('<button class="tab-button is-active" type="button" data-auth-tab="register">Register</button>', '<a class="tab-button is-active" href="/register">Register</a>')
register_html = register_html.replace('<button class="tab-button" type="button" data-auth-tab="login">Login</button>', '<a class="tab-button" href="/login">Login</a>')

# Add confirm password
register_form_old = '<div class="form-group full"><label class="label" for="register-password">Password</label><input class="field" id="register-password" type="password" minlength="8" required></div>'
register_form_new = register_form_old + '\n              <div class="form-group full"><label class="label" for="register-confirm-password">Confirm Password</label><input class="field" id="register-confirm-password" type="password" minlength="8" required></div>'
register_html = register_html.replace(register_form_old, register_form_new)
register_html = register_html.replace('<title>Login / Register | TridentWear</title>', '<title>Register | TridentWear</title>')


with open(os.path.join(html_dir, "login.html"), "w", encoding="utf-8") as f:
    f.write(login_html)

with open(os.path.join(html_dir, "register.html"), "w", encoding="utf-8") as f:
    f.write(register_html)


# 3. Create login.js and register.js
login_js = """import { post, saveAuthSession } from "../shared/api.js";
import { getCurrentUser, initSite, refreshAuthState, showToast } from "../shared/site.js";

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

function bindLogin() {
  const form = document.querySelector("[data-login-form]");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      const data = await post("/api/auth/login", {
        email: form.querySelector("#login-email").value.trim(),
        password: form.querySelector("#login-password").value.trim(),
      });
      saveAuthSession({ token: data.token, user: data.user });
      await refreshAuthState();
      showToast("Welcome back.");
      redirectAfterAuth(data.user);
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  bindLogin();
});
"""

register_js = """import { post, saveAuthSession } from "../shared/api.js";
import { getCurrentUser, initSite, refreshAuthState, showToast } from "../shared/site.js";

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

function bindRegister() {
  const form = document.querySelector("[data-register-form]");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      const data = await post("/api/auth/register", {
        name: form.querySelector("#register-name").value.trim(),
        email: form.querySelector("#register-email").value.trim(),
        password: form.querySelector("#register-password").value.trim(),
        confirm_password: form.querySelector("#register-confirm-password").value.trim(),
      });
      saveAuthSession({ token: data.token, user: data.user });
      await refreshAuthState();
      showToast("Account created successfully.");
      redirectAfterAuth(data.user);
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  bindRegister();
});
"""

with open(os.path.join(js_dir, "login.js"), "w", encoding="utf-8") as f:
    f.write(login_js)

with open(os.path.join(js_dir, "register.js"), "w", encoding="utf-8") as f:
    f.write(register_js)

try:
    os.remove(os.path.join(html_dir, "auth.html"))
    os.remove(os.path.join(js_dir, "auth.js"))
except Exception:
    pass

# 4. Update site.js setAccountUi string
site_js_path = os.path.join(shared_dir, "site.js")
with open(site_js_path, "r", encoding="utf-8") as f:
    site_js = f.read()

new_set_account_ui = """function setAccountUi() {
  const loginLink = document.querySelector("[data-login-link]");
  const registerLink = document.querySelector("[data-register-link]");
  const logoutButton = document.querySelector("[data-logout-button]");
  const adminLink = document.querySelector("[data-admin-link]");

  if (loginLink) {
    if (!currentUser) {
      loginLink.textContent = "Login";
      loginLink.setAttribute("href", "/login");
      loginLink.hidden = false;
      if (registerLink) registerLink.hidden = false;
    } else if (currentUser.role === "admin") {
      loginLink.textContent = "Admin";
      loginLink.setAttribute("href", "/admin");
      loginLink.hidden = false;
      if (registerLink) registerLink.hidden = true;
    } else {
      loginLink.textContent = currentUser.name.split(" ")[0];
      loginLink.setAttribute("href", "/products");
      loginLink.hidden = false;
      if (registerLink) registerLink.hidden = true;
    }
  }
  if (logoutButton) logoutButton.hidden = !currentUser;
  if (adminLink) adminLink.hidden = !(currentUser && currentUser.role === "admin");
}"""

site_js = re.sub(
    r'function setAccountUi\(\) \{.*?\n\}', 
    new_set_account_ui, 
    site_js, 
    flags=re.DOTALL
)

with open(site_js_path, "w", encoding="utf-8") as f:
    f.write(site_js)

# 5. Update header-tools across all HTML files
old_tools = '''<div class="header-tools">
        <a class="utility-pill" href="/auth" data-account-link>Login</a>
        <a class="utility-pill" href="/cart">Cart <span class="cart-badge" data-cart-count>0</span></a>
        <button class="utility-pill" type="button" data-logout-button hidden>Logout</button>
      </div>'''

new_tools = '''<div class="header-tools">
        <a class="utility-pill" href="/login" data-login-link>Login</a>
        <a class="utility-pill" href="/register" data-register-link>Sign Up</a>
        <a class="utility-pill" href="/cart">Cart <span class="cart-badge" data-cart-count>0</span></a>
        <button class="utility-pill" type="button" data-logout-button hidden>Logout</button>
      </div>'''

for html_file in glob.glob(os.path.join(html_dir, "*.html")):
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Simple regex replacing in case spacing varies
    content = re.sub(
        r'<div class="header-tools">\s*<a class="utility-pill" href="/auth" data-account-link>Login</a>\s*<a class="utility-pill" href="/cart">Cart <span class="cart-badge" data-cart-count>0</span></a>\s*<button class="utility-pill" type="button" data-logout-button hidden>Logout</button>\s*</div>',
        new_tools,
        content
    )

    # Some footer links also might point to /auth, let's fix them to /login
    content = content.replace('href="/auth"', 'href="/login"')

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)

print("done")
