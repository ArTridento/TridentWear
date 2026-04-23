import re

with open(r'd:\TridentWear\index.html', 'r', encoding='utf-8') as f:
    index_header = re.search(r'<header class="site-header"[^>]*>.*?</header>', f.read(), re.DOTALL).group(0)

with open(r'd:\TridentWear\about.html', 'r', encoding='utf-8') as f:
    about_header = re.search(r'<header class="site-header"[^>]*>.*?</header>', f.read(), re.DOTALL).group(0)

if index_header == about_header:
    print("They are identical.")
else:
    print("They are different.")
