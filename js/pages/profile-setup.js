import { post, saveAuthSession, getAuthSession } from "../shared/api.js?v=9";
import { initSite, showToast, getCurrentUser } from "../shared/site.js?v=9";

function nextPath() {
  const params = new URLSearchParams(window.location.search);
  return params.get("next") || "";
}

window.addEventListener("DOMContentLoaded", async () => {
  // Don't call initSite here — it would trigger the profile gate redirect loop.
  // Just check auth session directly.
  const { getAuthSession } = await import("../shared/api.js?v=9");
  const session = getAuthSession();
  if (!session?.user) {
    window.location.href = "login.html";
    return;
  }

  // Pre-fill name if available
  const nameEl = document.getElementById("setup-name-display");
  if (nameEl && session.user.name) nameEl.textContent = session.user.name;

  const form = document.querySelector("[data-setup-form]");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const titleRadio = form.querySelector("input[name='title']:checked");
    const gender = titleRadio ? titleRadio.value : "Other";

    const mobile = document.getElementById("setup-mobile")?.value.trim() || "";
    if (mobile && !/^[0-9]{10}$/.test(mobile)) {
      showToast("Enter a valid 10-digit mobile number.", "error");
      return;
    }

    const btn = form.querySelector("button[type='submit']");
    btn.disabled = true;
    btn.textContent = "Saving...";

    try {
      const result = await post("/api/auth/profile/setup", { gender, phone: mobile || null });

      // Update session with completed user data so guard won't trigger
      const currentSession = getAuthSession();
      if (currentSession && result.user) {
        saveAuthSession({ ...currentSession, user: { ...currentSession.user, ...result.user, profile_completed_status: true } });
      }

      showToast("Profile setup complete! Welcome to TridentWear 🎉", "success");

      setTimeout(() => {
        const next = nextPath();
        window.location.href = next || "profile.html";
      }, 900);
    } catch (err) {
      showToast(err.message || "Something went wrong. Try again.", "error");
      btn.disabled = false;
      btn.textContent = "Complete Setup";
    }
  });
});

