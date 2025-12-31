def get_order_status(order_id: str) -> dict:
    return {
        "ORD123": {"status": "DELIVERED", "signed_at": "2025-12-30T06:30:00"},
        "ORD456": {"status": "IN_TRANSIT"}
    }.get(order_id, {"status": "NOT_FOUND"})