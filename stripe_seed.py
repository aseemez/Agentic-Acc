import stripe
import os
import random
from datetime import datetime, timedelta

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

# fake customers
customer_names = [
    "Acme Corp", "Beta Ltd", "Gamma Inc",
    "Delta Co", "Epsilon LLC", "Zeta Solutions"
]

print("Creating customers...")
customer_ids = []
for name in customer_names:
    customer = stripe.Customer.create(
        name=name,
        email=f"{name.lower().replace(' ', '')}@example.com",
        description=f"Test customer: {name}"
    )
    customer_ids.append(customer.id)
    print(f"  Created: {name} ({customer.id})")

# fake charges against those customers
print("\nCreating charges...")
descriptions = [
    "Software License", "Consulting Fee", "Monthly Retainer",
    "Project Payment", "Service Fee", "Annual Subscription"
]

for i in range(30):
    amount = random.randint(1000, 50000)
    customer_id = random.choice(customer_ids)
    
    # attach test card to customer first
    payment_method = stripe.PaymentMethod.create(
        type="card",
        card={"token": "tok_visa"}
    )
    stripe.PaymentMethod.attach(
        payment_method.id,
        customer=customer_id
    )
    
    # now charge using payment intent
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency="usd",
        customer=customer_id,
        payment_method=payment_method.id,
        description=random.choice(descriptions),
        confirm=True,
        off_session=True
    )
    print(f"  Charge: ${amount/100:.2f} ({intent.id})")