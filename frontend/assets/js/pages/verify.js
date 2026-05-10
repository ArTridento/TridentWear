import { post } from "../shared/api.js?v=9";
import { initSite, pageUrl, showToast } from "../shared/site.js?v=9";

window.addEventListener("DOMContentLoaded", async () => {
  await initSite();

  const params = new URLSearchParams(window.location.search);
  const email = params.get("email");
  const display = document.getElementById("verify-email-display");
  if (display && email) {
    display.textContent = "Enter the 6-digit OTP sent to ";
    const strong = document.createElement("strong");
    strong.textContent = email;
    display.appendChild(strong);
  }
  
  const form = document.querySelector("[data-verify-form]");
  if (!form) return;
  
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
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
      await post("/api/auth/otp/verify-email", { email, otp });
      showToast("Account activated successfully! Please login.", "success");
      setTimeout(() => {
        window.location.href = pageUrl("/login");
      }, 1500);
    } catch (err) {
      showToast(err.message, "error");
      btn.disabled = false;
      btn.textContent = "Verify & Activate";
    }
  });
});
