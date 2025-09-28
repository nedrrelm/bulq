"""
Seed data for the Bulq application.
This module contains example data to populate the database for development and testing.
"""

from sqlalchemy.orm import Session
from models import User, Group, Store, Run, Product, ProductBid
from database import SessionLocal
import uuid
from decimal import Decimal

def create_seed_data():
    """Create example data for development and testing."""
    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(User).first():
            print("Seed data already exists, skipping...")
            return

        # Create Users
        users_data = [
            {"name": "Alice Johnson", "email": "alice@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"},
            {"name": "Carol Davis", "email": "carol@example.com"},
            {"name": "Dave Wilson", "email": "dave@example.com"},
        ]

        users = []
        for user_data in users_data:
            user = User(**user_data)
            db.add(user)
            users.append(user)

        db.flush()  # Get IDs without committing

        # Create Stores
        stores_data = [
            {"name": "Costco Wholesale"},
            {"name": "Sam's Club"},
            {"name": "BJ's Wholesale Club"},
            {"name": "Restaurant Depot"},
        ]

        stores = []
        for store_data in stores_data:
            store = Store(**store_data)
            db.add(store)
            stores.append(store)

        db.flush()

        # Create Groups
        groups_data = [
            {"name": "College Friends", "created_by": users[0].id},
            {"name": "Neighborhood Watch", "created_by": users[1].id},
            {"name": "Office Lunch Club", "created_by": users[2].id},
        ]

        groups = []
        for group_data in groups_data:
            group = Group(**group_data)
            db.add(group)
            groups.append(group)

        db.flush()

        # Add group memberships
        # College Friends: Alice, Bob, Carol
        groups[0].members.extend([users[0], users[1], users[2]])
        # Neighborhood Watch: Bob, Carol, Dave
        groups[1].members.extend([users[1], users[2], users[3]])
        # Office Lunch Club: Alice, Carol, Dave
        groups[2].members.extend([users[0], users[2], users[3]])

        # Create Products for different stores
        products_data = [
            # Costco products
            {"store_id": stores[0].id, "name": "Kirkland Olive Oil (3L)", "base_price": Decimal("24.99")},
            {"store_id": stores[0].id, "name": "Organic Quinoa (4.5kg)", "base_price": Decimal("18.99")},
            {"store_id": stores[0].id, "name": "Rotisserie Chicken", "base_price": Decimal("4.99")},
            {"store_id": stores[0].id, "name": "Paper Towels (12-pack)", "base_price": Decimal("19.99")},

            # Sam's Club products
            {"store_id": stores[1].id, "name": "Member's Mark Detergent (5.5kg)", "base_price": Decimal("16.98")},
            {"store_id": stores[1].id, "name": "Fresh Salmon Fillet (2kg)", "base_price": Decimal("32.98")},
            {"store_id": stores[1].id, "name": "Bulk Rice (9kg)", "base_price": Decimal("14.98")},

            # BJ's products
            {"store_id": stores[2].id, "name": "Wellsley Farms Coffee (1.4kg)", "base_price": Decimal("12.99")},
            {"store_id": stores[2].id, "name": "Fresh Berries Mix (1kg)", "base_price": Decimal("8.99")},
        ]

        products = []
        for product_data in products_data:
            product = Product(**product_data)
            db.add(product)
            products.append(product)

        db.flush()

        # Create Runs
        runs_data = [
            {
                "group_id": groups[0].id,
                "store_id": stores[0].id,
                "state": "active"
            },
            {
                "group_id": groups[1].id,
                "store_id": stores[1].id,
                "state": "planning"
            },
            {
                "group_id": groups[2].id,
                "store_id": stores[0].id,
                "state": "confirmed"
            },
        ]

        runs = []
        for run_data in runs_data:
            run = Run(**run_data)
            db.add(run)
            runs.append(run)

        db.flush()

        # Create Product Bids
        bids_data = [
            # Run 1 (College Friends at Costco) - Active
            {"user_id": users[0].id, "run_id": runs[0].id, "product_id": products[0].id, "quantity": 2, "interested_only": False},
            {"user_id": users[1].id, "run_id": runs[0].id, "product_id": products[0].id, "quantity": 1, "interested_only": False},
            {"user_id": users[2].id, "run_id": runs[0].id, "product_id": products[1].id, "quantity": 1, "interested_only": False},
            {"user_id": users[0].id, "run_id": runs[0].id, "product_id": products[2].id, "quantity": 3, "interested_only": False},
            {"user_id": users[1].id, "run_id": runs[0].id, "product_id": products[3].id, "quantity": 0, "interested_only": True},

            # Run 2 (Neighborhood Watch at Sam's Club) - Planning
            {"user_id": users[1].id, "run_id": runs[1].id, "product_id": products[4].id, "quantity": 0, "interested_only": True},
            {"user_id": users[2].id, "run_id": runs[1].id, "product_id": products[5].id, "quantity": 2, "interested_only": False},
            {"user_id": users[3].id, "run_id": runs[1].id, "product_id": products[6].id, "quantity": 1, "interested_only": False},

            # Run 3 (Office Lunch Club at Costco) - Confirmed
            {"user_id": users[0].id, "run_id": runs[2].id, "product_id": products[0].id, "quantity": 1, "interested_only": False},
            {"user_id": users[2].id, "run_id": runs[2].id, "product_id": products[2].id, "quantity": 4, "interested_only": False},
            {"user_id": users[3].id, "run_id": runs[2].id, "product_id": products[2].id, "quantity": 2, "interested_only": False},
        ]

        for bid_data in bids_data:
            bid = ProductBid(**bid_data)
            db.add(bid)

        # Commit all changes
        db.commit()
        print("✅ Seed data created successfully!")
        print(f"Created {len(users)} users, {len(groups)} groups, {len(stores)} stores")
        print(f"Created {len(products)} products, {len(runs)} runs, {len(bids_data)} bids")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating seed data: {e}")
        raise
    finally:
        db.close()

def clear_seed_data():
    """Clear all data from the database (useful for testing)."""
    db = SessionLocal()

    try:
        # Delete in reverse order of dependencies
        db.query(ProductBid).delete()
        db.query(Product).delete()
        db.query(Run).delete()

        # Clear many-to-many relationships
        for group in db.query(Group).all():
            group.members.clear()

        db.query(Group).delete()
        db.query(Store).delete()
        db.query(User).delete()

        db.commit()
        print("✅ All seed data cleared!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing seed data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_seed_data()
    else:
        create_seed_data()