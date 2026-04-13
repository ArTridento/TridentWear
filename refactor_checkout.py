import os
import re

app_py_path = r'd:\TridentWear\backend\app.py'
with open(app_py_path, 'r', encoding='utf-8') as f:
    app_py = f.read()

# 1. Add /checkout route
checkout_route = """
@pages_router.get("/checkout", include_in_schema=False)
def serve_checkout_page() -> FileResponse:
    return html_response("checkout.html")
"""

if "/checkout" not in app_py:
    app_py = app_py.replace('def serve_cart_page() -> FileResponse:\n    return html_response("cart.html")', 'def serve_cart_page() -> FileResponse:\n    return html_response("cart.html")\n' + checkout_route)

# Add "checkout": "/checkout" to legacy mapping just in case
if '"checkout": "/checkout"' not in app_py:
    app_py = app_py.replace('"cart": "/cart",', '"cart": "/cart",\n        "checkout": "/checkout",')

# 2. Require user in POST /orders
if 'if not user:\n        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED' not in app_py:
    app_py = app_py.replace(
        'user = get_session_user(request)',
        'user = get_session_user(request)\n    if not user:\n        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="You must be logged in to place an order.")'
    )

with open(app_py_path, 'w', encoding='utf-8') as f:
    f.write(app_py)

# 3. Create checkout.html based on cart.html
cart_html_path = r'd:\TridentWear\frontend\html\cart.html'
checkout_html_path = r'd:\TridentWear\frontend\html\checkout.html'

with open(cart_html_path, 'r', encoding='utf-8') as f:
    cart_html = f.read()

# Make checkout.html
checkout_html = cart_html.replace('data-page="cart"', 'data-page="checkout"')
checkout_html = checkout_html.replace('<title>Cart | TridentWear</title>', '<title>Checkout | TridentWear</title>')
checkout_html = checkout_html.replace('src="../js/pages/cart.js"', 'src="../js/pages/checkout.js"')
checkout_html = checkout_html.replace('<h1 class="page-title">Your Trident <span class="accent">cart</span>.</h1>', '<h1 class="page-title">Complete your <span class="accent">order</span>.</h1>')

# For checkout.html, remove the cart list (left side) and replace it with a simple summary or just leave order summary
checkout_html = re.sub(r'<article class="cart-card reveal-left">.*?</article>', '', checkout_html, flags=re.DOTALL)
checkout_html = checkout_html.replace('class="checkout-panel reveal-right"', 'class="checkout-panel reveal-scale" style="width: 100%; max-width: 800px; margin: 0 auto;"')

with open(checkout_html_path, 'w', encoding='utf-8') as f:
    f.write(checkout_html)


# 4. Modify cart.html to remove the checkout form and add "Proceed to Checkout" button
cart_html = re.sub(
    r'<form class="form-grid" data-checkout-form>.*?</form>',
    '<div class="form-group full"><a class="btn btn-primary" href="/checkout" style="display: block; text-align: center;">Proceed to Checkout</a></div>',
    cart_html,
    flags=re.DOTALL
)
# And we can leave data-cart-summary alone in cart.html or just let it be. But update page-copy
cart_html = cart_html.replace('Guest checkout is enabled, and signed-in users get customer details prefilled automatically.', 'Review your selections before completing checkout.')

with open(cart_html_path, 'w', encoding='utf-8') as f:
    f.write(cart_html)


# 5. Create checkout.js and update cart.js
cart_js_path = r'd:\TridentWear\frontend\js\pages\cart.js'
checkout_js_path = r'd:\TridentWear\frontend\js\pages\checkout.js'

with open(cart_js_path, 'r', encoding='utf-8') as f:
    cart_js = f.read()

# Make checkout.js
# checkout.js handles form submission. It will need loadCart, etc.
checkout_js = cart_js
checkout_js = checkout_js.replace('function bindCartActions() {', 'function ignoreCart() {')
# Add Whatsapp button logic
whatsapp_snippet = """
    try {
      const data = await postWithFallback(["/api/orders", "/orders"], payload);
      
      const whatsappText = encodeURIComponent(`Hello TridentWear! I placed an order ${data.order_id}.`);
      const whatsappLink = `https://wa.me/919876543210?text=${whatsappText}`;
      
      clearCart();
      form.reset();
      showToast(`Order placed. ID: ${data.order_id}`);
      document.querySelector("[data-order-status]").innerHTML = `
        <div class="helper-note success" style="display: flex; flex-direction: column; gap: 0.5rem;">
          <strong>${data.order_id}</strong>
          <span>Your order has been saved successfully!</span>
          <a class="btn btn-secondary" href="${whatsappLink}" target="_blank">Order via WhatsApp</a>
        </div>
      `;
    }
"""
checkout_js = re.sub(r'try \{\s*const data = await postWithFallback.*?\}', whatsapp_snippet.strip(), checkout_js, flags=re.DOTALL)
# Checkout.js doesn't need to renderCart list (which doesn't exist). But it calls renderSummary() and bindCheckout().
with open(checkout_js_path, 'w', encoding='utf-8') as f:
    f.write(checkout_js)

# Modify cart.js
# Remove the bindCheckout call and definition
cart_js = re.sub(r'function prefillUser\(\).*?\}\s*function bindCheckout\(\).*?\}', '', cart_js, flags=re.DOTALL)
cart_js = cart_js.replace('prefillUser();\n  renderCart();\n  bindCheckout();', 'renderCart();')
cart_js = cart_js.replace('const button = document.querySelector("[data-checkout-button]");', '')
cart_js = cart_js.replace('button.disabled = true;', '')
cart_js = cart_js.replace('button.disabled = false;', '')

with open(cart_js_path, 'w', encoding='utf-8') as f:
    f.write(cart_js)

print("Checkout refactoring complete!")
