import os
import re

dir_path = r'd:\TridentWear'

# Regex pattern to match the <div class="nav-dropdown">...</div> block
# We use re.DOTALL so .* can match newlines
pattern = re.compile(r'<div class="nav-dropdown">\s*<a class="nav-link nav-dropdown-trigger" href="products\.html" data-nav-link="products">\s*Products.*?</div>\s*</div>', re.DOTALL)

replacement = '<a class="nav-link" href="products.html" data-nav-link="products">Products</a>'

count = 0
for root, dirs, files in os.walk(dir_path):
    # Exclude node_modules or other unrelated dirs if any, but it's safe to just check .html
    if 'node_modules' in dirs:
        dirs.remove('node_modules')
    
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content, num_subs = pattern.subn(replacement, content)
            
            if num_subs > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print(f"Updated {file}")

print(f"Total files updated: {count}")
