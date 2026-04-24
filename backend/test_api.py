#!/usr/bin/env python3
"""
Automated API Testing Script for TridentWear Backend

Usage:
    python test_api.py

This script tests all major API endpoints and validates responses.
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"
ACCESS_TOKEN = None
PRODUCT_ID = None
ORDER_ID = None
RAZORPAY_ORDER_ID = None

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'


def print_test(name: str):
    """Print test name"""
    print(f"\n{Colors.BLUE}→ {name}{Colors.END}")


def print_success(message: str):
    """Print success message"""
    print(f"  {Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    print(f"  {Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    print(f"  {Colors.YELLOW}ℹ {message}{Colors.END}")


def test_health() -> bool:
    """Test health check endpoint"""
    print_test("Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            data = response.json()
            print_success(f"Server is healthy (v{data.get('version')})")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running on http://localhost:8000?")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_register() -> bool:
    """Test user registration"""
    print_test("User Registration")

    global ACCESS_TOKEN

    data = {
        "email": "testuser@example.com",
        "password": "TestPassword123",
        "full_name": "Test User",
        "phone": "9876543210",
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=data, timeout=5)

        if response.status_code == 201:
            result = response.json()
            ACCESS_TOKEN = result.get("access_token")
            print_success(f"User registered: {data['email']}")
            print_info(f"Access token: {ACCESS_TOKEN[:20]}...")
            return True
        elif response.status_code == 400:
            # User might already exist, try login instead
            print_info("User already exists, will use login instead")
            return True
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_error(response.text)
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_login() -> bool:
    """Test user login"""
    print_test("User Login")

    global ACCESS_TOKEN

    if ACCESS_TOKEN:
        print_info("Already have access token from registration")
        return True

    data = {
        "email": "testuser@example.com",
        "password": "TestPassword123",
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data, timeout=5)

        if response.status_code == 200:
            result = response.json()
            ACCESS_TOKEN = result.get("access_token")
            print_success(f"Login successful")
            print_info(f"Access token: {ACCESS_TOKEN[:20]}...")
            return True
        else:
            print_error(f"Login failed: {response.status_code}")
            print_error(response.text)
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_get_current_user() -> bool:
    """Test get current user"""
    print_test("Get Current User")

    if not ACCESS_TOKEN:
        print_error("No access token available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=5)

        if response.status_code == 200:
            user = response.json()
            print_success(f"Retrieved user: {user.get('email')}")
            print_info(f"User ID: {user.get('id')}")
            return True
        else:
            print_error(f"Failed to get user: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_get_products() -> bool:
    """Test get all products"""
    print_test("Get All Products")

    global PRODUCT_ID

    try:
        response = requests.get(
            f"{BASE_URL}/api/products?skip=0&limit=10",
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            total = result.get("total", 0)
            items = result.get("items", [])

            print_success(f"Retrieved {len(items)} products (total: {total})")

            if items:
                PRODUCT_ID = items[0].get("id")
                print_info(f"First product: {items[0].get('name')} (ID: {PRODUCT_ID[:8]}...)")
                return True
            else:
                print_info("No products found - will try to create one")
                return True

        else:
            print_error(f"Failed to get products: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_create_product() -> bool:
    """Test create product (admin)"""
    print_test("Create Product (Admin)")

    global PRODUCT_ID

    if not ACCESS_TOKEN:
        print_error("No access token available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    data = {
        "name": "Test T-Shirt",
        "description": "Premium test T-shirt",
        "sku": f"TEST-TSHIRT-{int(requests.utils.requests.time.time())}",
        "price": 499.99,
        "cost": 250.00,
        "discount_percent": 10,
        "stock": 100,
        "category": "Clothing",
        "size": "M",
        "color": "Black",
        "material": "100% Cotton",
        "is_active": True,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/products",
            json=data,
            headers=headers,
            timeout=5
        )

        if response.status_code == 201:
            product = response.json()
            PRODUCT_ID = product.get("id")
            print_success(f"Product created: {product.get('name')}")
            print_info(f"Product ID: {PRODUCT_ID[:8]}...")
            return True
        elif response.status_code == 403:
            print_info("Not admin - skipping product creation")
            return True
        else:
            print_error(f"Failed to create product: {response.status_code}")
            print_error(response.text)
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_create_order() -> bool:
    """Test create order"""
    print_test("Create Order")

    global ORDER_ID, PRODUCT_ID

    if not ACCESS_TOKEN:
        print_error("No access token available")
        return False

    if not PRODUCT_ID:
        print_error("No product ID available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    data = {
        "items": [
            {
                "product_id": PRODUCT_ID,
                "quantity": 1,
                "size": "M",
                "color": "Black",
            }
        ],
        "shipping_name": "Test User",
        "shipping_email": "test@example.com",
        "shipping_phone": "9876543210",
        "shipping_address": "123 Test Street",
        "shipping_city": "Mumbai",
        "shipping_state": "Maharashtra",
        "shipping_postal_code": "400001",
        "shipping_country": "India",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/orders",
            json=data,
            headers=headers,
            timeout=5
        )

        if response.status_code == 201:
            order = response.json()
            ORDER_ID = order.get("id")
            print_success(f"Order created: {ORDER_ID[:8]}...")
            print_info(f"Total: ₹{order.get('total')}")
            print_info(f"Subtotal: ₹{order.get('subtotal')}")
            print_info(f"Tax: ₹{order.get('tax')}")
            print_info(f"Shipping: ₹{order.get('shipping_cost')}")
            return True
        else:
            print_error(f"Failed to create order: {response.status_code}")
            print_error(response.text)
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_get_orders() -> bool:
    """Test get user orders"""
    print_test("Get User Orders")

    if not ACCESS_TOKEN:
        print_error("No access token available")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    try:
        response = requests.get(
            f"{BASE_URL}/api/orders?skip=0&limit=10",
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            total = result.get("total", 0)
            items = result.get("items", [])

            print_success(f"Retrieved {len(items)} orders (total: {total})")

            if items:
                print_info(f"Latest order: {items[0].get('id')[:8]}...")
            return True

        else:
            print_error(f"Failed to get orders: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_create_razorpay_order() -> bool:
    """Test create Razorpay order"""
    print_test("Create Razorpay Order")

    global RAZORPAY_ORDER_ID

    if not ACCESS_TOKEN or not ORDER_ID:
        print_error("Missing access token or order ID")
        return False

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

    data = {"order_id": ORDER_ID}

    try:
        response = requests.post(
            f"{BASE_URL}/api/payments/create-order",
            json=data,
            headers=headers,
            timeout=5
        )

        if response.status_code == 200:
            result = response.json()
            RAZORPAY_ORDER_ID = result.get("razorpay_order_id")
            amount = result.get("amount")

            print_success(f"Razorpay order created")
            print_info(f"Order ID: {RAZORPAY_ORDER_ID}")
            print_info(f"Amount: ₹{amount/100} (in paisa: {amount})")
            return True
        else:
            print_error(f"Failed to create Razorpay order: {response.status_code}")
            print_error(response.text)
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"TridentWear API - Automated Testing")
    print(f"{'='*60}{Colors.END}\n")

    tests = [
        ("Server Health", test_health),
        ("User Registration/Login", lambda: test_register() and test_login()),
        ("Get Current User", test_get_current_user),
        ("Get Products", test_get_products),
        ("Create Product", test_create_product),
        ("Create Order", test_create_order),
        ("Get Orders", test_get_orders),
        ("Create Razorpay Order", test_create_razorpay_order),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"Exception: {str(e)}")
            failed += 1

    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"Test Results: {Colors.GREEN}{passed} passed{Colors.END}, {Colors.RED}{failed} failed{Colors.END}")
    print(f"{'='*60}{Colors.END}\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
