import os
import re

js_dir = r"d:\TridentWear\frontend\js"
known_pages = ['products', 'product', 'admin', 'login', 'cart', 'track', 'wishlist', 'register', 'about', 'contact', 'checkout']

for root, dirs, files in os.walk(js_dir):
    for f in files:
        if f.endswith(".js"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # replace "/products" -> "products.html" in anything doing strings
            for page in known_pages:
                # regex to match "/page" or "/page?..."
                pattern = r'(["\'])/' + page + r'((\?[^"\']*)?["\'])'
                replacement = r'\g<1>' + page + r'.html\2'
                content = re.sub(pattern, replacement, content)
                
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)

print("Updated JS paths.")
