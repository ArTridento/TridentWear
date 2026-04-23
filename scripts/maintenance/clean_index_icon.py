import os
import re

filepath = r'd:\TridentWear\index.html'
with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

content = re.sub(r'<i class="fa-jelly-fill fa-regular fa-user"></i>', '<i class="fa-regular fa-user"></i>', content)
content = re.sub(r'class="fa-jelly-fill fa-regular fa-user"', 'class="fa-regular fa-user"', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated index.html")
