import os, re

with open('verify.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('Verify Email | TridentWear', 'Profile Setup | TridentWear')
html = html.replace('js/pages/verify.js', 'js/pages/profile-setup.js')
html = html.replace('data-page="verify"', 'data-page="profile-setup"')

new_form = '''
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

html = re.sub(r'<div class="auth-box">.*?</form>\s*</div>\s*<div class="auth-social"[^>]*>', new_form, html, flags=re.DOTALL)

with open('profile-setup.html', 'w', encoding='utf-8') as f:
    f.write(html)
