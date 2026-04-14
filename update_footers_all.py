"""
Bulk-update all HTML pages with the new premium footer.
Run from project root: python update_footers_all.py
"""
import re
from pathlib import Path

HTML_DIR = Path(__file__).resolve().parent / "frontend" / "html"

SKIP_FILES = {"index.html"}  # Already updated manually

NEW_FOOTER = '''  <footer class="site-footer">
    <div class="footer-top-strip">
      <div class="container">
        <span>🇮🇳 Proudly Made in India — Wear the Pride</span>
      </div>
    </div>
    <div class="container footer-main">
      <div class="footer-brand-col">
        <div class="brand">
          <span class="brand-name"><span class="brand-trident">Trident</span><span class="brand-wear">Wear</span></span>
          <span class="brand-tagline">T-Shirt Collections</span>
        </div>
        <p class="footer-note">Premium men's clothing built for India's everyday uniform. Heritage quality, modern fit.</p>
        <div class="footer-trust-badges">
          <span class="footer-badge"><i class="fa-solid fa-indian-rupee-sign"></i> COD Available</span>
          <span class="footer-badge"><i class="fa-solid fa-rotate-left"></i> 30-Day Returns</span>
        </div>
      </div>
      <div class="footer-col">
        <h3 class="footer-title">Need Help</h3>
        <div class="footer-links">
          <a href="contact.html"><i class="fa-regular fa-envelope footer-link-icon"></i>Contact Us</a>
          <a href="track.html"><i class="fa-solid fa-location-dot footer-link-icon"></i>Track Order</a>
          <a href="returns.html"><i class="fa-solid fa-rotate-left footer-link-icon"></i>Returns &amp; Refunds</a>
          <a href="contact.html"><i class="fa-regular fa-circle-question footer-link-icon"></i>FAQs</a>
        </div>
      </div>
      <div class="footer-col">
        <h3 class="footer-title">Company</h3>
        <div class="footer-links">
          <a href="about.html">About Us</a>
          <a href="products.html">Shop All</a>
          <a href="wishlist.html">Wishlist</a>
          <a href="contact.html">Careers</a>
        </div>
      </div>
      <div class="footer-col">
        <h3 class="footer-title">More Info</h3>
        <div class="footer-links">
          <a href="terms.html">T&amp;C</a>
          <a href="privacy.html">Privacy Policy</a>
          <a href="shipping.html">Shipping Policy</a>
          <a href="returns.html">Returns Policy</a>
        </div>
      </div>
      <div class="footer-col">
        <h3 class="footer-title">Contact Us</h3>
        <div class="footer-links">
          <a href="mailto:hello@tridentwear.com"><i class="fa-regular fa-envelope footer-link-icon"></i>hello@tridentwear.com</a>
          <a href="tel:+919876543210"><i class="fa-solid fa-phone footer-link-icon"></i>+91 98765 43210</a>
          <a href="https://wa.me/919876543210" target="_blank" rel="noreferrer"><i class="fa-brands fa-whatsapp footer-link-icon"></i>WhatsApp</a>
        </div>
        <div class="footer-app-badges">
          <a class="footer-app-btn" href="#"><i class="fa-brands fa-google-play"></i> Google Play</a>
          <a class="footer-app-btn" href="#"><i class="fa-brands fa-apple"></i> App Store</a>
        </div>
      </div>
    </div>
    <div class="footer-middle">
      <div class="container footer-middle-inner">
        <div class="footer-payment">
          <span class="footer-payment-label">100% Secure Payment:</span>
          <div class="footer-payment-icons">
            <span class="payment-pill"><i class="fa-brands fa-google-pay"></i> GPay</span>
            <span class="payment-pill"><i class="fa-brands fa-cc-mastercard"></i> Mastercard</span>
            <span class="payment-pill"><i class="fa-brands fa-cc-visa"></i> Visa</span>
            <span class="payment-pill"><i class="fa-solid fa-money-bill-wave"></i> COD</span>
            <span class="payment-pill">UPI</span>
          </div>
        </div>
        <div class="footer-social-wrap">
          <span class="footer-payment-label">Follow Us:</span>
          <div class="footer-socials">
            <a class="footer-social-link" href="https://instagram.com" target="_blank" rel="noreferrer" aria-label="Instagram"><i class="fa-brands fa-instagram"></i></a>
            <a class="footer-social-link" href="https://twitter.com" target="_blank" rel="noreferrer" aria-label="Twitter/X"><i class="fa-brands fa-x-twitter"></i></a>
            <a class="footer-social-link" href="https://youtube.com" target="_blank" rel="noreferrer" aria-label="YouTube"><i class="fa-brands fa-youtube"></i></a>
            <a class="footer-social-link" href="https://facebook.com" target="_blank" rel="noreferrer" aria-label="Facebook"><i class="fa-brands fa-facebook-f"></i></a>
          </div>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="footer-bottom">
        <span class="footer-copy">&copy; 2026 TridentWear. All rights reserved.</span>
        <div class="footer-bottom-links">
          <a href="privacy.html">Privacy</a>
          <a href="terms.html">Terms</a>
          <a href="shipping.html">Shipping</a>
        </div>
      </div>
    </div>
  </footer>'''

# Match the footer block  
FOOTER_PATTERN = re.compile(
    r'<footer class="site-footer">.*?</footer>',
    re.DOTALL
)

updated = []
skipped = []

for html_file in sorted(HTML_DIR.glob("*.html")):
    if html_file.name in SKIP_FILES:
        skipped.append(html_file.name)
        continue
    
    content = html_file.read_text(encoding="utf-8")
    
    if '<footer class="site-footer">' not in content:
        skipped.append(f"{html_file.name} (no footer)")
        continue
    
    new_content = FOOTER_PATTERN.sub(NEW_FOOTER, content, count=1)
    
    if new_content != content:
        html_file.write_text(new_content, encoding="utf-8")
        updated.append(html_file.name)
    else:
        skipped.append(f"{html_file.name} (no match)")

print(f"\nUpdated {len(updated)} files:")
for f in updated:
    print(f"   + {f}")

print(f"\nSkipped {len(skipped)} files:")
for f in skipped:
    print(f"   - {f}")
