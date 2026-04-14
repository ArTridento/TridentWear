import os

html_dir = r"d:\TridentWear\frontend\html"
fa_link = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">\n</head>'

for f in os.listdir(html_dir):
    if f.endswith(".html"):
        path = os.path.join(html_dir, f)
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        
        if "font-awesome" not in content:
            content = content.replace("</head>", fa_link)
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)

print("Injected FontAwesome.")
