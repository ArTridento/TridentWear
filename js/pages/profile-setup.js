import { post } from "../shared/api.js";
import { initSite, showToast, getCurrentUser, refreshAuthState } from "../shared/site.js";

function nextPath() {
  const params = new URLSearchParams(window.location.search);
  return params.get("next") || "";
}

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  
  const user = getCurrentUser();
  if (!user) {
    window.location.href = "login.html";
    return;
  }
  
  const form = document.querySelector("[data-setup-form]");
  if (!form) return;
  
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    // Get checked radio button value
    const titleRadio = form.querySelector("input[name='title']:checked");
    const gender = titleRadio ? titleRadio.value : "Other";
    
    const mobile = document.getElementById("setup-mobile")?.value.trim() || "";
    
    const btn = form.querySelector("button[type='submit']");
    btn.disabled = true;
    btn.textContent = "Saving...";
    
    try {
      await post("/api/auth/profile/setup", { gender, phone: mobile || null });
      await refreshAuthState();
      showToast("Profile completed! Redirecting...", "success");
      
      setTimeout(() => {
        const next = nextPath();
        if (next) window.location.href = next;
        else window.location.href = "profile.html";
      }, 1000);
    } catch (err) {
      showToast(err.message, "error");
      btn.disabled = false;
      btn.textContent = "Complete Setup";
    }
  });
});
