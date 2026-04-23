import os
import re

dir_path = r'd:\TridentWear'
# Regex to match <i class="fa-solid fa-circle-user"></i> even with newlines
pattern = re.compile(r'<i class="fa-solid fa-circle-user"></i>', re.DOTALL)
replacement = '<i class="fa-regular fa-user"></i>'

count = 0
for root, dirs, files in os.walk(dir_path):
    if 'node_modules' in dirs:
        dirs.remove('node_modules')
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            new_content, num_subs = pattern.subn(replacement, content)
            if num_subs > 0:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                count += 1
                print(f"Updated {file}")

print(f"Total files updated: {count}")
