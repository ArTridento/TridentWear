import os, re

with open('login.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Make verify.html
verify_html = html.replace('Login | TridentWear', 'Verify Email | TridentWear')
verify_html = verify_html.replace('js/pages/login.js', 'js/pages/verify.js')
verify_html = verify_html.replace('data-page="login"', 'data-page="verify"')

new_verify_form = '''
<div class="auth-box">
  <h1 class="auth-title">Verify Email</h1>
  <p class="auth-subtitle">Enter the 6-digit OTP sent to your email to activate your account.</p>
  <form class="auth-form" data-verify-form>
    <div class="form-group">
      <label class="form-label">OTP Code</label>
      <input type="text" id="verify-otp" class="form-control" placeholder="123456" required minlength="6" maxlength="6">
    </div>
    <button type="submit" class="btn btn-primary" style="width: 100%">Verify & Activate</button>
  </form>
</div>
<div class="auth-social" style="display:none;">
'''
verify_html = re.sub(r'<div class="auth-box">.*?</form>\s*</div>\s*<div class="auth-social"[^>]*>', new_verify_form, verify_html, flags=re.DOTALL)

with open('verify.html', 'w', encoding='utf-8') as f:
    f.write(verify_html)

# Make profile-setup.html from verify.html
setup_html = verify_html.replace('Verify Email | TridentWear', 'Profile Setup | TridentWear')
setup_html = setup_html.replace('js/pages/verify.js', 'js/pages/profile-setup.js')
setup_html = setup_html.replace('data-page="verify"', 'data-page="profile-setup"')

new_setup_form = '''
<div class="auth-box">
  <h1 class="auth-title">Almost Done!</h1>
  <p class="auth-subtitle">Please complete your profile to continue.</p>
  <form class="auth-form" data-setup-form>
    <div class="form-group">
      <label class="form-label">Title</label>
      <div style="display:flex; gap:1rem; margin-top:0.5rem;">
        <label style="cursor:pointer;"><input type="radio" name="title" value="Mr" checked> Mr.</label>
        <label style="cursor:pointer;"><input type="radio" name="title" value="Miss"> Miss.</label>
        <label style="cursor:pointer;"><input type="radio" name="title" value="Other"> Other</label>
      </div>
    </div>
    <div class="form-group">
      <label class="form-label">Mobile Number (Optional)</label>
      <input type="text" id="setup-mobile" class="form-control" placeholder="10 digit number">
    </div>
    <button type="submit" class="btn btn-primary" style="width: 100%">Complete Setup</button>
  </form>
</div>
<div class="auth-social" style="display:none;">
'''
setup_html = re.sub(r'<div class="auth-box">.*?</form>\s*</div>\s*<div class="auth-social"[^>]*>', new_setup_form, setup_html, flags=re.DOTALL)

with open('profile-setup.html', 'w', encoding='utf-8') as f:
    f.write(setup_html)
