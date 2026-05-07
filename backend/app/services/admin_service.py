from typing import Dict, Any, List
from app.services.order_service import load_orders

def get_analytics_data() -> Dict[str, Any]:
    orders = load_orders()
    total_orders = len(orders)
    total_revenue = sum(o.get("subtotal", 0) for o in orders)
    unique_customers = len(set(o.get("customer", {}).get("email") for o in orders if o.get("customer", {}).get("email")))
    
    product_sales = {}
    for o in orders:
        for item in o.get("items", []):
            name = item.get("name")
            qty = item.get("qty", 1)
            if name:
                product_sales[name] = product_sales.get(name, 0) + qty
                
    top_products = [{"name": k, "sold": v} for k, v in sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    return {
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "customers": unique_customers,
        "top_products": top_products
    }
