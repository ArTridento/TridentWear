import { post } from "../shared/api.js?v=9";
import { initSite, showToast } from "../shared/site.js?v=9";

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();
  
  const form = document.querySelector("[data-verify-form]");
  if (!form) return;
  
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const params = new URLSearchParams(window.location.search);
    const email = params.get("email");
    if (!email) {
      showToast("No email found to verify. Please register again.", "error");
      return;
    }
    
    const otp = document.getElementById("verify-otp").value.trim();
    if (otp.length < 6) {
      showToast("Please enter a valid 6-digit OTP", "error");
      return;
    }
    
    const btn = form.querySelector("button[type='submit']");
    btn.disabled = true;
    btn.textContent = "Verifying...";
    
    try {
      await post("/verify-otp", { email, otp });
      showToast("Account activated successfully! Please login.", "success");
      // Redirect to login
      setTimeout(() => {
        window.location.href = "login.html";
      }, 1500);
    } catch (err) {
      showToast(err.message, "error");
      btn.disabled = false;
      btn.textContent = "Verify & Activate";
    }
  });
});
