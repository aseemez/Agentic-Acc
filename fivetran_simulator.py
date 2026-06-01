import stripe
import os
import pymongo
from datetime import datetime

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
client = pymongo.MongoClient(os.environ["MONGODB_URI"])
db = client["accounting"]

# fivetran uses its own collections with specific schema
# we mirror that exactly
stripe_charges = db["stripe_charges"]
stripe_customers = db["stripe_customers"]

# clear existing stripe data
stripe_charges.delete_many({})
stripe_customers.delete_many({})

print("Pulling customers from Stripe...")
customers = stripe.Customer.list(limit=100)
customer_docs = []

for c in customers.auto_paging_iter():
    customer_docs.append({
        # fivetran schema fields
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "created": datetime.fromtimestamp(c.created),
        "description": c.description,
        # fivetran metadata fields
        "_fivetran_synced": datetime.now(),
        "_fivetran_deleted": False
    })

if customer_docs:
    stripe_customers.insert_many(customer_docs)
    print(f"  Loaded {len(customer_docs)} customers into MongoDB")

print("\nPulling charges from Stripe...")
charges = stripe.Charge.list(limit=100)
charge_docs = []

for c in charges.auto_paging_iter():
    charge_docs.append({
        # fivetran schema fields
        "id": c.id,
        "amount": c.amount / 100,
        "currency": c.currency.upper(),
        "customer_id": c.customer,
        "description": c.description,
        "status": c.status,
        "created": datetime.fromtimestamp(c.created),
        "paid": c.paid,
        # fivetran metadata fields
        "_fivetran_synced": datetime.now(),
        "_fivetran_deleted": False
    })

if charge_docs:
    stripe_charges.insert_many(charge_docs)
    print(f"  Loaded {len(charge_docs)} charges into MongoDB")

print("\nDone! Stripe data is now in MongoDB.")
print(f"Collections: stripe_charges ({db.stripe_charges.count_documents({})}), stripe_customers ({db.stripe_customers.count_documents({})})")