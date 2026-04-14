import os
import re

html_dir = r"d:\TridentWear\frontend\html"

for f in os.listdir(html_dir):
    if f.endswith(".html"):
        path = os.path.join(html_dir, f)
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        
        # Replace href="/products" etc with href="products.html"
        content = re.sub(r'href="/([a-zA-Z0-9_-]+)(#[a-zA-Z0-9_-]+)?"', r'href="\1.html\2"', content)
        content = re.sub(r'href="/(\?[^"]+)?"', r'href="index.html\1"', content)
        
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)

print("Completed updating HTML links.")
