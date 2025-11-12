import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone, timedelta
import random
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Sample data
DISTRICTS = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune", "Hyderabad", "Ahmedabad"]
STATES = ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "West Bengal", "Maharashtra", "Telangana", "Gujarat"]
FIRST_NAMES = ["Rajesh", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rahul", "Deepika", "Suresh", "Kavita"]
LAST_NAMES = ["Kumar", "Sharma", "Patel", "Singh", "Reddy", "Desai", "Mehta", "Gupta", "Verma", "Joshi"]
CARD_TYPES = ["BPL", "APL", "Antyodaya"]
ITEMS = [
    {"name": "Rice", "unit": "kg"},
    {"name": "Wheat", "unit": "kg"},
    {"name": "Sugar", "unit": "kg"},
    {"name": "Cooking Oil", "unit": "liter"},
    {"name": "Kerosene", "unit": "liter"}
]

async def seed_database():
    print("Starting database seeding...")
    
    # Clear existing data
    await db.users.delete_many({})
    await db.cards.delete_many({})
    await db.shops.delete_many({})
    await db.transactions.delete_many({})
    await db.fraud_alerts.delete_many({})
    await db.admins.delete_many({})
    
    print("✓ Cleared existing data")
    
    # Create shops
    shops = []
    for i in range(10):
        shop = {
            "id": f"shop-{i+1}",
            "shop_id": f"PDS-{random.randint(1000, 9999)}",
            "name": f"Fair Price Shop {i+1}",
            "district": DISTRICTS[i % len(DISTRICTS)],
            "state": STATES[i % len(STATES)],
            "location": {"lat": 28.0 + random.random() * 10, "lng": 77.0 + random.random() * 10},
            "officer_name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "phone": f"+91-{random.randint(7000000000, 9999999999)}",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        shops.append(shop)
    
    await db.shops.insert_many(shops)
    print(f"✓ Created {len(shops)} shops")
    
    # Create users and cards
    users = []
    cards = []
    
    for i in range(50):
        district = random.choice(DISTRICTS)
        state = STATES[DISTRICTS.index(district)]
        card_type = random.choice(CARD_TYPES)
        
        # Create some intentional duplicates for fraud detection
        if i > 40 and random.random() < 0.3:
            # Duplicate Aadhaar
            aadhaar = users[random.randint(0, 20)]["aadhaar_id"]
        else:
            aadhaar = f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        
        if i > 35 and random.random() < 0.2:
            # Duplicate address
            address = users[random.randint(0, 15)]["address"]
        else:
            address = f"{random.randint(1, 999)} {random.choice(['MG Road', 'Main Street', 'Park Avenue', 'Gandhi Nagar', 'Station Road'])}, {district}"
        
        # Income mismatch for some BPL cards
        if card_type == "BPL" and random.random() < 0.15:
            income = random.randint(100000, 200000)  # Too high for BPL
        elif card_type == "BPL":
            income = random.randint(20000, 80000)
        elif card_type == "APL":
            income = random.randint(80000, 300000)
        else:
            income = random.randint(10000, 50000)
        
        user = {
            "id": f"user-{i+1}",
            "aadhaar_id": aadhaar,
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
            "address": address,
            "district": district,
            "state": state,
            "family_size": random.randint(1, 8),
            "income": income,
            "card_type": card_type,
            "phone": f"+91-{random.randint(7000000000, 9999999999)}",
            "status": random.choice(["active"] * 8 + ["suspended", "flagged"]),
            "verification_status": random.choice(["verified"] * 7 + ["pending"] * 2 + ["rejected"]),
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 365))).isoformat()
        }
        users.append(user)
        
        # Create 1-2 cards per user (some have multiple for fraud)
        num_cards = 2 if random.random() < 0.1 else 1
        for j in range(num_cards):
            card = {
                "id": f"card-{i+1}-{j+1}",
                "card_number": f"RC-{random.randint(100000, 999999)}",
                "user_id": user["id"],
                "issue_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(365, 1095))).isoformat(),
                "validity": (datetime.now(timezone.utc) + timedelta(days=random.randint(365, 730))).isoformat(),
                "status": "active",
                "created_at": user["created_at"]
            }
            cards.append(card)
    
    await db.users.insert_many(users)
    await db.cards.insert_many(cards)
    print(f"✓ Created {len(users)} users and {len(cards)} ration cards")
    
    # Create transactions
    transactions = []
    for i in range(200):
        user = random.choice(users)
        user_cards = [c for c in cards if c["user_id"] == user["id"]]
        if user_cards:
            card = random.choice(user_cards)
            shop = random.choice(shops)
            
            # Create some abnormal transaction patterns
            num_items = random.randint(1, 5)
            if random.random() < 0.05:  # 5% anomalies
                num_items = random.randint(8, 15)  # Too many items
            
            txn_items = []
            total = 0
            for _ in range(num_items):
                item = random.choice(ITEMS)
                quantity = random.randint(1, 10)
                price = random.uniform(10, 100)
                txn_items.append({
                    "name": item["name"],
                    "quantity": quantity,
                    "unit": item["unit"],
                    "price": round(price, 2)
                })
                total += quantity * price
            
            transaction = {
                "id": f"txn-{i+1}",
                "card_number": card["card_number"],
                "user_id": user["id"],
                "shop_id": shop["shop_id"],
                "items": txn_items,
                "total_amount": round(total, 2),
                "transaction_date": (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))).isoformat()
            }
            transactions.append(transaction)
    
    await db.transactions.insert_many(transactions)
    print(f"✓ Created {len(transactions)} transactions")
    
    print("\n✅ Database seeding completed successfully!")
    print("\nSummary:")
    print(f"  - Users: {len(users)}")
    print(f"  - Cards: {len(cards)}")
    print(f"  - Shops: {len(shops)}")
    print(f"  - Transactions: {len(transactions)}")
    print("\nNote: Fraud detection will automatically flag suspicious users when they are accessed.")

if __name__ == "__main__":
    asyncio.run(seed_database())
