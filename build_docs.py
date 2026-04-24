import os
import shutil
import re

def build():
    print("Building TridentWear for GitHub Pages...")
    
    # 1. Clean docs directory
    if os.path.exists("docs"):
        shutil.rmtree("docs")
    
    # 2. Copy frontend to docs
    shutil.copytree("frontend", "docs")
    
    # 3. Read components
    try:
        with open("frontend/components/header.html", "r", encoding="utf-8") as f:
            header_html = f.read()
        with open("frontend/components/footer.html", "r", encoding="utf-8") as f:
            footer_html = f.read()
    except Exception as e:
        print(f"Error reading components: {e}")
        header_html = "<!-- Header Component Missing -->"
        footer_html = "<!-- Footer Component Missing -->"

    # 4. Process all HTML, JS, CSS files
    for root, _, files in os.walk("docs"):
        for file in files:
            if file.endswith(".html"):
                filepath = os.path.join(root, file)
                
                # Determine relative path prefix to root
                rel_dir = os.path.relpath("docs", root)
                if rel_dir == ".":
                    prefix = "./"
                else:
                    prefix = rel_dir.replace("\\", "/") + "/"
                
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Replace components
                content = content.replace("{{ component:header }}", header_html)
                content = content.replace("{{ component:footer }}", footer_html)
                
                # Replace absolute paths with relative paths
                content = re.sub(r'href="/(?!/)', f'href="{prefix}', content)
                content = re.sub(r'src="/(?!/)', f'src="{prefix}', content)
                content = re.sub(r'action="/(?!/)', f'action="{prefix}', content)
                
                content = content.replace("url('/assets/", f"url('{prefix}assets/")
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                    
            elif file.endswith(".js") or file.endswith(".css"):
                filepath = os.path.join(root, file)
                
                rel_dir = os.path.relpath("docs", root)
                if rel_dir == ".":
                    prefix = "./"
                else:
                    prefix = rel_dir.replace("\\", "/") + "/"
                    
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Fix paths in JS and CSS
                content = re.sub(r"fetch\('/(?!/)", f"fetch('{prefix}", content)
                content = re.sub(r"url\('/(?!/)", f"url('{prefix}", content)
                content = re.sub(r"url\(\"/(?!/)", f"url(\"{prefix}", content)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)

    print("Build complete. docs/ is ready to be deployed.")

if __name__ == "__main__":
    build()
