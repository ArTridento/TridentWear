import re
with open(r'd:\TridentWear\backend\app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to find the definition of legacy_html_routes and everything after it up to validate_product_fields
# Let's locate `def legacy_html_routes` and `async def create_product`
start_marker = "def legacy_html_routes"
end_marker = "async def create_product"

idx1 = text.find(start_marker)
idx2 = text.find(end_marker)

if idx1 != -1 and idx2 != -1:
    before = text[:idx1]
    after = text[idx2:]
    
    middle = """def legacy_html_routes(page_name: str, request: Request):
    mapping = {
        "index": "/",
        "shop": "/products",
        "products": "/products",
        "product": "/product",
        "cart": "/cart",
        "login": "/login",
        "register": "/register",
        "about": "/about",
        "contact": "/contact",
        "admin": "/admin",
        "privacy": "/privacy",
        "terms": "/terms",
        "returns": "/returns",
        "shipping": "/shipping",
    }
    target = mapping.get(page_name)
    if not target:
        return FileResponse(HTML_DIR / "404.html", status_code=404)
    if target == "/admin":
        return serve_admin_page(request)
    return RedirectResponse(url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@auth_router.get("/me")
def get_auth_state(request: Request) -> Dict[str, Any]:
    user = get_session_user(request)
    return {"authenticated": bool(user), "user": serialize_user(user) if user else None}


@auth_router.post("/register")
def register(payload: RegisterPayload, request: Request) -> Dict[str, Any]:
    name = payload.name.strip()
    email = validate_email(payload.email)
    password = payload.password.strip()

    if len(name) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name must be at least 2 characters.")
    if len(password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters.")
    if payload.confirm_password is not None and payload.confirm_password.strip() != password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match.")
    if find_user_by_email(email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with that email already exists.")

    users = load_users()
    new_user = {
        "id": next_id(users),
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": "customer",
        "created_at": now_iso(),
    }
    users.append(new_user)
    save_users(users)

    token = jwt.encode(
        {"sub": str(new_user["id"]), "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256",
    )

    return {"success": True, "message": "Account created successfully.", "token": token, "user": serialize_user(new_user)}


@auth_router.post("/login")
def login(payload: LoginPayload, request: Request) -> Dict[str, Any]:
    email = validate_email(payload.email)
    password = payload.password.strip()
    user = find_user_by_email(email)

    if not user or not verify_password(password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")

    token = jwt.encode(
        {"sub": str(user["id"]), "exp": datetime.now(timezone.utc) + timedelta(days=7)},
        JWT_SECRET,
        algorithm="HS256",
    )

    return {"success": True, "message": "Signed in successfully.", "token": token, "user": serialize_user(user)}


@auth_router.post("/logout")
def logout(request: Request) -> Dict[str, Any]:
    return {"success": True, "message": "Signed out."}


@products_router.get("/products")
def get_products(category: Optional[str] = None, featured: Optional[bool] = None) -> Dict[str, Any]:
    products = load_products()

    if category:
        category_value = category.strip().lower()
        products = [product for product in products if product["category"] == category_value]

    if featured is not None:
        products = [product for product in products if product["featured"] is featured]

    return {"success": True, "count": len(products), "products": products}


@products_router.get("/products/{product_id}")
def get_single_product(product_id: int) -> Dict[str, Any]:
    for product in load_products():
        if product["id"] == product_id:
            return {"success": True, "product": product}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")


def validate_product_fields(
    name: str,
    category: str,
    price: str,
    description: str,
    tag: str,
    sizes: str,
    stock: str,
    featured: str,
) -> Dict[str, Any]:
    product_name = name.strip()
    category_value = category.strip().lower()
    description_value = description.strip()

    if len(product_name) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product name must be at least 3 characters.")
    if category_value not in {"tshirt", "shirt"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category must be tshirt or shirt.")

    try:
        price_value = int(float(price))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be a valid number.") from error
    if price_value <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be greater than zero.")

    try:
        stock_value = max(int(float(stock or 0)), 0)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock must be a valid number.") from error

    return {
        "name": product_name,
        "category": category_value,
        "price": price_value,
        "description": description_value,
        "tag": tag.strip(),
        "sizes": normalize_sizes(sizes),
        "stock": stock_value,
        "featured": normalize_bool(featured),
    }


@admin_router.post("/products")
"""
    with open(r'd:\TridentWear\backend\app.py', 'w', encoding='utf-8') as f:
        f.write(before + middle + after[len("async def create_product"):])
    print("Fixed!")
else:
    print("Failed to find markers")
