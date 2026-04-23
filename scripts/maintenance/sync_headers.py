import os
import re

dir_path = r'd:\TridentWear'
index_path = os.path.join(dir_path, 'index.html')

# 1. Read index.html and extract the header
with open(index_path, 'r', encoding='utf-8', errors='ignore') as f:
    index_content = f.read()

# Match the <header> block. Assuming it starts with <header class="site-header" and ends with </header>
header_match = re.search(r'<header class="site-header"[^>]*>.*?</header>', index_content, re.DOTALL)
if not header_match:
    print("Could not find header in index.html")
    exit(1)

header_html = header_match.group(0)

# 2. Iterate through all other .html files and replace their header
count = 0
for root, dirs, files in os.walk(dir_path):
    if 'node_modules' in dirs:
        dirs.remove('node_modules')
    for file in files:
        if file.endswith('.html') and file != 'index.html':
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Replace the old header with the new one
            new_content, num_subs = re.subn(r'<header class="site-header"[^>]*>.*?</header>', header_html, content, count=1, flags=re.DOTALL)
            
            if num_subs > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print(f"Updated header in {file}")

print(f"Total files updated: {count}")
