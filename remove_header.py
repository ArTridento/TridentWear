import re
import os

files = ['login.html', 'register.html', 'verify.html', 'profile-setup.html']
for filename in files:
    filepath = os.path.join('d:\\TridentWear', filename)
    if not os.path.exists(filepath): continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = re.sub(r'<header class="site-header">.*?</header>\s*', '', content, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Removed header from {filename}')
    else:
        print(f'No header found or already removed in {filename}')
