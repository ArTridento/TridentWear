import os
import re

html_dir = r"d:\TridentWear\frontend\html"

# The pattern we are looking for is the div of header-tools
# We want to replace it with a clean version with only icons

new_header_tools = '''<div class="header-tools">
        <a class="utility-pill" href="login.html" data-login-link title="Login"><i class="fa-sharp-duotone fa-solid fa-arrow-right-to-bracket"></i></a>
        <a class="utility-pill" href="register.html" data-register-link title="Register"><i class="fa-solid fa-user-plus"></i></a>
        <a class="utility-pill" href="cart.html" title="Cart"><i class="fa-sharp fa-solid fa-cart-shopping"></i> <span class="cart-badge" data-cart-count>0</span></a>
        <button class="utility-pill" type="button" data-logout-button title="Logout" hidden><i class="fa-sharp-duotone fa-solid fa-arrow-left-from-bracket"></i></button>
      </div>'''

for f in os.listdir(html_dir):
    if f.endswith(".html"):
        path = os.path.join(html_dir, f)
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
            
        # Regex to find header-tools div and its content
        content = re.sub(r'<div class="header-tools">.*?</div>', new_header_tools, content, flags=re.DOTALL)
        
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

print("Headers updated successfully.")
