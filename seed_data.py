# ── IMPORTS ──
# pymongo lets us talk to MongoDB
import pymongo

# random lets us pick random items from lists (for realistic fake data)
import random

# datetime lets us create realistic dates for transactions
from datetime import datetime, timedelta

# os lets us read environment variables
import os

# ── CONNECTION ──
# connect directly without .env for now since we know this works
client = pymongo.MongoClient(os.environ["MONGODB_URI"])

# select (or create) a database called "accounting"
# MongoDB creates it automatically when we first write to it
db = client["accounting"]

# ── FAKE DATA LISTS ──
# realistic vendor names a small business would actually pay
vendors = [
    "AWS", "Figma", "Notion", "Slack", "Zoom",
    "Office Supplies Co", "Nepal Airlines", "Kathmandu Coffee",
    "Print House", "Uber", "Google Workspace", "Canva"
]

# expense categories we'll use throughout the system
categories = ["Software", "Travel", "Office", "Marketing", "Utilities"]

# fake client names who owe us money
clients = [
    "Acme Corp", "Beta Ltd", "Gamma Inc",
    "Delta Co", "Epsilon LLC", "Zeta Solutions"
]

# ── GENERATE TRANSACTIONS ──
print("Creating transactions...")
transactions = []

for i in range(50):
    # create a random date within the last 90 days
    date = datetime.now() - timedelta(days=random.randint(0, 90))

    transactions.append({
        "type": "expense",
        "vendor": random.choice(vendors),
        "amount": round(random.uniform(10, 2000), 2),
        "currency": "USD",
        "category": random.choice(categories),
        "date": date,
        "status": "reconciled",
        "receipt_url": None,
        # audit_log tracks every action taken on this record
        # this is what makes auditing trivial later
        "audit_log": [{
            "action": "created",
            "by": "seed_script",
            "at": datetime.now()
        }]
    })

# ── GENERATE INVOICES ──
print("Creating invoices...")
invoices = []

for i in range(20):
    # invoice was issued sometime in the last 60 days
    issued = datetime.now() - timedelta(days=random.randint(0, 60))

    # payment is due 30 days after issue
    due = issued + timedelta(days=30)

    # figure out real status based on dates
    today = datetime.now()
    if due > today:
        status = random.choice(["paid", "unpaid"])
    else:
        status = random.choice(["paid", "overdue"])

    invoices.append({
        "type": "invoice",
        "client": random.choice(clients),
        "amount": round(random.uniform(500, 10000), 2),
        "currency": "USD",
        "issued_date": issued,
        "due_date": due,
        "status": status,
        # same audit trail pattern as transactions
        "audit_log": [{
            "action": "created",
            "by": "seed_script",
            "at": datetime.now()
        }]
    })

# ── INSERT INTO MONGODB ──
# clear existing data first so we don't get duplicates if we run this twice
db.transactions.delete_many({})
db.invoices.delete_many({})

# insert all our fake records
db.transactions.insert_many(transactions)
db.invoices.insert_many(invoices)

# ── CONFIRM ──
print(f"Created {db.transactions.count_documents({})} transactions")
print(f"Created {db.invoices.count_documents({})} invoices")
print(f"Overdue invoices: {db.invoices.count_documents({'status': 'overdue'})}")
print(f"Unpaid invoices: {db.invoices.count_documents({'status': 'unpaid'})}")
print("Done! Open MongoDB Compass to see your data.")