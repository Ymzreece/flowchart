def process_order(order_total: float, items):
    invoice = []
    if order_total > 100:
        invoice.append("apply_discount")
    else:
        invoice.append("standard_pricing")

    for item in items:
        invoice.append(f"ship_{item}")

    return invoice
