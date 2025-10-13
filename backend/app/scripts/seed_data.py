"""Seed data for the Bulq application.

This module contains example data to populate the database for development and testing.
"""

from decimal import Decimal

from ..auth import hash_password
from ..database import SessionLocal
from ..models import Group, Product, ProductAvailability, Run, RunParticipation, Store, User


def create_seed_data():
    """Create example data for development and testing."""
    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(User).first():
            print('Seed data already exists, skipping...')
            return

        # Create Users with hashed passwords
        password_hash = hash_password('password123')
        users_data = [
            {'name': 'Alice Johnson', 'email': 'alice@example.com', 'password_hash': password_hash, 'verified': True},
            {'name': 'Bob Smith', 'email': 'bob@example.com', 'password_hash': password_hash, 'verified': True},
            {'name': 'Carol Davis', 'email': 'carol@example.com', 'password_hash': password_hash, 'verified': False},
            {'name': 'Dave Wilson', 'email': 'dave@example.com', 'password_hash': password_hash, 'verified': True},
        ]

        users = []
        for user_data in users_data:
            user = User(**user_data)
            db.add(user)
            users.append(user)

        db.flush()  # Get IDs without committing

        # Create Stores
        stores_data = [
            {'name': 'Costco Wholesale', 'address': '123 Warehouse Way', 'verified': True},
            {'name': "Sam's Club", 'address': '456 Bulk Blvd', 'verified': True},
            {'name': "BJ's Wholesale Club", 'address': '789 Shopping Center', 'verified': False},
            {'name': 'Restaurant Depot', 'address': '321 Commercial St', 'verified': True},
        ]

        stores = []
        for store_data in stores_data:
            store = Store(**store_data)
            db.add(store)
            stores.append(store)

        db.flush()

        # Create Groups
        groups_data = [
            {'name': 'College Friends', 'created_by': users[0].id, 'is_joining_allowed': True},
            {'name': 'Neighborhood Watch', 'created_by': users[1].id, 'is_joining_allowed': True},
            {'name': 'Office Lunch Club', 'created_by': users[2].id, 'is_joining_allowed': True},
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

        # Create Products (store-agnostic)
        products_data = [
            {'name': 'Kirkland Olive Oil', 'brand': 'Kirkland', 'unit': '3L', 'verified': True, 'created_by': users[0].id},
            {'name': 'Organic Quinoa', 'brand': None, 'unit': '4.5kg', 'verified': True, 'created_by': users[0].id},
            {'name': 'Rotisserie Chicken', 'brand': None, 'unit': 'each', 'verified': True, 'created_by': users[1].id},
            {'name': 'Paper Towels', 'brand': None, 'unit': '12-pack', 'verified': False, 'created_by': users[1].id},
            {'name': 'Laundry Detergent', 'brand': "Member's Mark", 'unit': '5.5kg', 'verified': True, 'created_by': users[2].id},
            {'name': 'Fresh Salmon Fillet', 'brand': None, 'unit': '2kg', 'verified': True, 'created_by': users[2].id},
            {'name': 'Bulk Rice', 'brand': None, 'unit': '9kg', 'verified': True, 'created_by': users[3].id},
            {'name': 'Coffee Beans', 'brand': 'Wellsley Farms', 'unit': '1.4kg', 'verified': False, 'created_by': users[3].id},
            {'name': 'Fresh Berries Mix', 'brand': None, 'unit': '1kg', 'verified': True, 'created_by': users[0].id},
        ]

        products = []
        for product_data in products_data:
            product = Product(**product_data)
            db.add(product)
            products.append(product)

        db.flush()

        # Create Product Availabilities (prices at specific stores)
        availabilities_data = [
            # Costco
            {'product_id': products[0].id, 'store_id': stores[0].id, 'price': Decimal('24.99'), 'created_by': users[0].id},
            {'product_id': products[1].id, 'store_id': stores[0].id, 'price': Decimal('18.99'), 'created_by': users[0].id},
            {'product_id': products[2].id, 'store_id': stores[0].id, 'price': Decimal('4.99'), 'created_by': users[1].id},
            {'product_id': products[3].id, 'store_id': stores[0].id, 'price': Decimal('19.99'), 'created_by': users[1].id},
            # Sam's Club
            {'product_id': products[4].id, 'store_id': stores[1].id, 'price': Decimal('16.98'), 'created_by': users[2].id},
            {'product_id': products[5].id, 'store_id': stores[1].id, 'price': Decimal('32.98'), 'created_by': users[2].id},
            {'product_id': products[6].id, 'store_id': stores[1].id, 'price': Decimal('14.98'), 'created_by': users[3].id},
            # BJ's
            {'product_id': products[7].id, 'store_id': stores[2].id, 'price': Decimal('12.99'), 'created_by': users[3].id},
            {'product_id': products[8].id, 'store_id': stores[2].id, 'price': Decimal('8.99'), 'created_by': users[0].id},
        ]

        for availability_data in availabilities_data:
            availability = ProductAvailability(**availability_data)
            db.add(availability)

        db.flush()

        # Create Runs
        runs_data = [
            {'group_id': groups[0].id, 'store_id': stores[0].id, 'state': 'active', 'leader_id': users[0].id},
            {'group_id': groups[1].id, 'store_id': stores[1].id, 'state': 'planning', 'leader_id': users[1].id},
            {'group_id': groups[2].id, 'store_id': stores[0].id, 'state': 'confirmed', 'leader_id': users[2].id},
        ]

        runs = []
        for run_data in runs_data:
            run = Run(**run_data)
            db.add(run)
            runs.append(run)

        db.flush()

        # Create Run Participations
        participations_data = [
            # Run 1 participants
            {'run_id': runs[0].id, 'user_id': users[0].id},
            {'run_id': runs[0].id, 'user_id': users[1].id},
            {'run_id': runs[0].id, 'user_id': users[2].id},
            # Run 2 participants
            {'run_id': runs[1].id, 'user_id': users[1].id},
            {'run_id': runs[1].id, 'user_id': users[2].id},
            {'run_id': runs[1].id, 'user_id': users[3].id},
            # Run 3 participants
            {'run_id': runs[2].id, 'user_id': users[0].id},
            {'run_id': runs[2].id, 'user_id': users[2].id},
            {'run_id': runs[2].id, 'user_id': users[3].id},
        ]

        participations = []
        for participation_data in participations_data:
            participation = RunParticipation(**participation_data)
            db.add(participation)
            participations.append(participation)

        db.flush()

        # Create Product Bids (now using participation_id instead of user_id/run_id)
        from models import ProductBid
        bids_data = [
            # Run 1 (College Friends at Costco) - Active
            {'participation_id': participations[0].id, 'product_id': products[0].id, 'quantity': 2, 'interested_only': False},
            {'participation_id': participations[1].id, 'product_id': products[0].id, 'quantity': 1, 'interested_only': False},
            {'participation_id': participations[2].id, 'product_id': products[1].id, 'quantity': 1, 'interested_only': False},
            {'participation_id': participations[0].id, 'product_id': products[2].id, 'quantity': 3, 'interested_only': False},
            {'participation_id': participations[1].id, 'product_id': products[3].id, 'quantity': 0, 'interested_only': True},
            # Run 2 (Neighborhood Watch at Sam's Club) - Planning
            {'participation_id': participations[3].id, 'product_id': products[4].id, 'quantity': 0, 'interested_only': True},
            {'participation_id': participations[4].id, 'product_id': products[5].id, 'quantity': 2, 'interested_only': False},
            {'participation_id': participations[5].id, 'product_id': products[6].id, 'quantity': 1, 'interested_only': False},
            # Run 3 (Office Lunch Club at Costco) - Confirmed
            {'participation_id': participations[6].id, 'product_id': products[0].id, 'quantity': 1, 'interested_only': False},
            {'participation_id': participations[7].id, 'product_id': products[2].id, 'quantity': 4, 'interested_only': False},
            {'participation_id': participations[8].id, 'product_id': products[2].id, 'quantity': 2, 'interested_only': False},
        ]

        for bid_data in bids_data:
            bid = ProductBid(**bid_data)
            db.add(bid)

        # Commit all changes
        db.commit()
        print('✅ Seed data created successfully!')
        print(f'Created {len(users)} users, {len(groups)} groups, {len(stores)} stores')
        print(f'Created {len(products)} products, {len(runs)} runs, {len(bids_data)} bids')

    except Exception as e:
        db.rollback()
        print(f'❌ Error creating seed data: {e}')
        raise
    finally:
        db.close()


def clear_seed_data():
    """Clear all data from the database (useful for testing)."""
    db = SessionLocal()

    try:
        # Delete in reverse order of dependencies
        from models import ProductBid
        db.query(ProductBid).delete()
        db.query(RunParticipation).delete()
        db.query(ProductAvailability).delete()
        db.query(Product).delete()
        db.query(Run).delete()

        # Clear many-to-many relationships
        for group in db.query(Group).all():
            group.members.clear()

        db.query(Group).delete()
        db.query(Store).delete()
        db.query(User).delete()

        db.commit()
        print('✅ All seed data cleared!')

    except Exception as e:
        db.rollback()
        print(f'❌ Error clearing seed data: {e}')
        raise
    finally:
        db.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'clear':
        clear_seed_data()
    else:
        create_seed_data()
