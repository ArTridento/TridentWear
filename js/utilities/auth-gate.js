
export function promptLoginOverlay() {
  let modal = document.querySelector(".login-prompt-overlay");
  if (modal) modal.remove();
  
  modal = document.createElement("div");
  modal.className = "login-prompt-overlay";
  modal.innerHTML = `
    <div class="login-prompt-backdrop" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 9999; backdrop-filter: blur(4px);"></div>
    <div class="login-prompt-card" style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #fff; padding: 2rem; border-radius: 16px; width: 90%; max-width: 400px; z-index: 10000; box-shadow: 0 20px 40px rgba(0,0,0,0.2); text-align: center;">
      <div style="background:var(--primary); color:#fff; width:48px; height:48px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:1.25rem; margin:0 auto 1.5rem auto;">
        <i class="fa-solid fa-lock"></i>
      </div>
      <h3 style="font-size:1.5rem; font-weight:800; color:var(--gray-900); margin-bottom:0.75rem; letter-spacing:-0.02em;">Login to continue</h3>
      <p style="font-size:0.95rem; color:var(--gray-600); margin-bottom:2rem; line-height:1.5;">Join TridentWear to unlock your cart, wishlist, and exclusive checkout drops.</p>
      <div style="display:flex; gap:1rem; justify-content:center;">
        <button class="btn btn-outline" type="button" data-cancel style="flex:1;">Cancel</button>
        <button class="btn btn-primary" type="button" data-login style="flex:1;">Sign In</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  
  modal.querySelector("[data-cancel]").addEventListener("click", () => modal.remove());
  modal.querySelector("[data-login]").addEventListener("click", () => {
    window.location.href = \`login.html?next=\${encodeURIComponent(window.location.pathname)}\`;
  });
}
