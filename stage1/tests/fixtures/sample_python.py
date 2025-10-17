def process_order(order):
    if order.total > 100:
        apply_discount(order)
    else:
        apply_standard_pricing(order)

    for item in order.items:
        ship_item(item)

    return order.receipt()
