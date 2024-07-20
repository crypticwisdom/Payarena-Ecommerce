product_status_choices = (
    ('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending'), ('declined', 'Declined'),
    ('checked', 'Checked'), ('approve', 'Approve')
)

cart_status_choices = (
    ('open', 'Open'), ('closed', 'Closed'), ('discard', 'Discard')
)

payment_status_choices = (
    ('success', 'Success'), ('pending', 'Pending'), ('failed', 'Failed'), ('refunded', 'Refunded')
)

order_status_choices = (
    ('cancelled', 'Cancelled'), ('processed', 'Processed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'),
    ('returned', 'Returned'), ('paid', 'Paid'), ('refunded', 'Refunded'), ('pending', 'Pending')
)

order_entry_status = (
    ("packed", "Packed"), ("shipped", "Shipped"), ("delivered", "Delivered"), ("received", "Received"),
    ("cancelled", "Cancelled"), ("returned", "Returned"), ("refunded", "Refunded")
)


