from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import SplitResult, urlsplit, urlunsplit


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
DOCS_DIR = BASE_DIR / "docs"
COMPONENTS_DIR = FRONTEND_DIR / "components"

ROUTE_SOURCES = {
    "": FRONTEND_DIR / "index.html",
    "products": FRONTEND_DIR / "pages" / "shop" / "products.html",
    "cart": FRONTEND_DIR / "pages" / "shop" / "cart.html",
    "product": FRONTEND_DIR / "pages" / "shop" / "product.html",
    "checkout": FRONTEND_DIR / "pages" / "shop" / "checkout.html",
    "wishlist": FRONTEND_DIR / "pages" / "shop" / "wishlist.html",
    "login": FRONTEND_DIR / "pages" / "account" / "login.html",
    "register": FRONTEND_DIR / "pages" / "account" / "register.html",
    "profile": FRONTEND_DIR / "pages" / "account" / "profile.html",
    "profile-setup": FRONTEND_DIR / "pages" / "account" / "profile-setup.html",
    "verify": FRONTEND_DIR / "pages" / "account" / "verify.html",
    "about": FRONTEND_DIR / "pages" / "info" / "about.html",
    "contact": FRONTEND_DIR / "pages" / "info" / "contact.html",
    "admin": FRONTEND_DIR / "pages" / "admin" / "admin.html",
    "privacy": FRONTEND_DIR / "pages" / "legal" / "privacy.html",
    "terms": FRONTEND_DIR / "pages" / "legal" / "terms.html",
    "returns": FRONTEND_DIR / "pages" / "legal" / "returns.html",
    "shipping": FRONTEND_DIR / "pages" / "legal" / "shipping.html",
    "track": FRONTEND_DIR / "pages" / "support" / "track.html",
}

STATIC_ROUTE_TARGETS = {
    "/": "",
    "/products": "products/",
    "/cart": "cart/",
    "/product": "product/",
    "/product-detail": "product/",
    "/product-detail.html": "product/",
    "/checkout": "checkout/",
    "/wishlist": "wishlist/",
    "/login": "login/",
    "/register": "register/",
    "/profile": "profile/",
    "/profile-setup": "profile-setup/",
    "/verify": "verify/",
    "/about": "about/",
    "/contact": "contact/",
    "/admin": "admin/",
    "/privacy": "privacy/",
    "/terms": "terms/",
    "/returns": "returns/",
    "/shipping": "shipping/",
    "/track": "track/",
}

URL_ATTR_PATTERN = re.compile(r'(?P<attr>href|src|action)=(?P<quote>["\'])(?P<value>.*?)(?P=quote)')
CSS_URL_PATTERN = re.compile(r"url\((?P<quote>['\"]?)(?P<value>/[^)'\"]+)(?P=quote)\)")


def site_prefix(destination: Path) -> str:
    depth = len(destination.relative_to(DOCS_DIR).parent.parts)
    return "./" if depth == 0 else "../" * depth


def load_component(name: str) -> str:
    return (COMPONENTS_DIR / f"{name}.html").read_text(encoding="utf-8")


def rewrite_path(raw_value: str, prefix: str) -> str:
    if not raw_value:
        return raw_value

    lowered = raw_value.lower()
    if raw_value.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return raw_value
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", raw_value) or raw_value.startswith("//"):
        return raw_value

    parsed = urlsplit(raw_value)
    path = parsed.path or ""
    if not path.startswith("/"):
        return raw_value

    if path in STATIC_ROUTE_TARGETS:
        new_path = prefix + STATIC_ROUTE_TARGETS[path]
    else:
        new_path = prefix + path.lstrip("/")

    rebuilt = SplitResult(
        scheme="",
        netloc="",
        path=new_path or prefix,
        query=parsed.query,
        fragment=parsed.fragment,
    )
    return urlunsplit(rebuilt)


def rewrite_attr_urls(content: str, prefix: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        value = rewrite_path(match.group("value"), prefix)
        return f'{match.group("attr")}={match.group("quote")}{value}{match.group("quote")}'

    return URL_ATTR_PATTERN.sub(replacer, content)


def rewrite_css_urls(content: str, prefix: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        quote = match.group("quote") or ""
        value = rewrite_path(match.group("value"), prefix)
        return f"url({quote}{value}{quote})"

    return CSS_URL_PATTERN.sub(replacer, content)


def render_html(source: Path, destination: Path, header_html: str, footer_html: str) -> None:
    prefix = site_prefix(destination)
    content = source.read_text(encoding="utf-8")
    content = content.replace("{{ component:header }}", header_html)
    content = content.replace("{{ component:footer }}", footer_html)
    content = rewrite_attr_urls(content, prefix)
    content = rewrite_css_urls(content, prefix)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def rewrite_static_assets(file_path: Path) -> None:
    prefix = site_prefix(file_path)
    content = file_path.read_text(encoding="utf-8")

    if file_path.suffix == ".css":
        content = rewrite_css_urls(content, prefix)

    file_path.write_text(content, encoding="utf-8")


def build() -> None:
    print("Building TridentWear for GitHub Pages...")

    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)

    shutil.copytree(FRONTEND_DIR, DOCS_DIR)

    if (BASE_DIR / ".nojekyll").exists():
        shutil.copy2(BASE_DIR / ".nojekyll", DOCS_DIR / ".nojekyll")

    header_html = load_component("header")
    footer_html = load_component("footer")

    for html_file in DOCS_DIR.rglob("*.html"):
        source = FRONTEND_DIR / html_file.relative_to(DOCS_DIR)
        render_html(source, html_file, header_html, footer_html)

    for asset_file in DOCS_DIR.rglob("*"):
        if asset_file.suffix in {".css"}:
            rewrite_static_assets(asset_file)

    for route, source in ROUTE_SOURCES.items():
        if route:
            destination = DOCS_DIR / route / "index.html"
        else:
            destination = DOCS_DIR / "index.html"
        render_html(source, destination, header_html, footer_html)

    render_html(
        FRONTEND_DIR / "pages" / "error" / "404.html",
        DOCS_DIR / "404.html",
        header_html,
        footer_html,
    )

    print("Build complete. docs/ is ready to be deployed.")


if __name__ == "__main__":
    build()
