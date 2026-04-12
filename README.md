# Trident Premium Store

Trident is a premium streetwear store project built with a plain HTML/CSS/JavaScript frontend and a FastAPI backend. The current build includes a dark luxury UI, product catalog, product detail pages, cart and checkout, login/register, admin product management, and a local contact inbox.

## Stack

- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI
- Data storage: JSON files in `db/`
- Auth: Cookie-based sessions with local seeded users
- Admin uploads: Stored in `frontend/images/uploads/`

## Project Structure

```text
TridentWear/
|-- backend/
|   |-- app.py
|   `-- routes/
|-- db/
|   |-- contacts.json
|   |-- orders.json
|   |-- products.json
|   `-- users.json
|-- frontend/
|   |-- css/
|   |   |-- style.css
|   |   `-- styles.css
|   |-- html/
|   |   |-- about.html
|   |   |-- admin.html
|   |   |-- auth.html
|   |   |-- cart.html
|   |   |-- contact.html
|   |   |-- index.html
|   |   |-- product.html
|   |   `-- shop.html
|   |-- images/
|   |   `-- uploads/
|   `-- js/
|       |-- pages/
|       |-- shared/
|       |-- products.json
|       `-- script.js
`-- requirements.txt
```

## Features

- Premium dark UI using the shared `frontend/css/styles.css` theme
- Home page with hero and featured products
- Products page with live filtering
- Product detail page with size selection
- Cart page with local cart persistence and checkout form
- Login/register with local session auth
- Admin panel with add, edit, delete, featured toggle, and image upload
- Contact form that writes to `db/contacts.json`
- Orders saved to `db/orders.json`

## Local Setup

1. Install Python 3.11 or newer.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the server from the project root:

   ```bash
   uvicorn backend.app:app --reload
   ```

4. Open:

   - Storefront: [http://127.0.0.1:8000](http://127.0.0.1:8000)
   - Products: [http://127.0.0.1:8000/products](http://127.0.0.1:8000/products)
   - Admin: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

## Seeded Admin Account

- Email: `admin@trident.local`
- Password: `TridentAdmin123!`

## API Overview

- `GET /api/auth/me`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/products`
- `GET /api/products/{id}`
- `POST /api/admin/products`
- `PUT /api/admin/products/{id}`
- `DELETE /api/admin/products/{id}`
- `POST /api/orders`
- `POST /api/contact`

## Notes

- `db/products.json` is the product source of truth.
- `frontend/js/products.json` is kept as a mirrored catalog snapshot for compatibility.
- This workspace did not have Python installed during implementation, so the code was prepared for local run but not executed in this environment.
