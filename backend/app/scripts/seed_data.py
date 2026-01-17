"""Repository-agnostic seed data for development and testing."""

from datetime import UTC, datetime, timedelta

from app.core.run_state import RunState


def create_seed_data(db_session=None):
    """Create test data using modular repositories.

    Works with both database and memory modes by using repository factory functions.
    Handles backdating of timestamps for realistic test scenarios.

    Args:
        db_session: SQLAlchemy session (for database mode) or None (for memory mode)
    """
    from app.repositories import (
        get_bid_repository,
        get_group_repository,
        get_product_repository,
        get_run_repository,
        get_shopping_repository,
        get_store_repository,
        get_user_repository,
    )

    # Get repository instances
    user_repo = get_user_repository(db_session)
    group_repo = get_group_repository(db_session)
    store_repo = get_store_repository(db_session)
    product_repo = get_product_repository(db_session)
    run_repo = get_run_repository(db_session)
    bid_repo = get_bid_repository(db_session)
    shopping_repo = get_shopping_repository(db_session)

    # Create test users
    alice = user_repo.create_user('Alice Johnson', 'alice', 'hashed_password')
    bob = user_repo.create_user('Bob Smith', 'bob', 'hashed_password')
    carol = user_repo.create_user('Carol Davis', 'carol', 'hashed_password')
    test_user = user_repo.create_user('Test User', 'test', 'hashed_password')
    test_user.is_admin = True

    # Additional users for testing merge functionality
    david = user_repo.create_user('David Williams', 'david', 'hashed_password')
    emily = user_repo.create_user('Emily Brown', 'emily', 'hashed_password')
    frank = user_repo.create_user('Frank Miller', 'frank', 'hashed_password')

    # Create test groups
    friends_group = group_repo.create_group('Test Friends', alice.id)
    work_group = group_repo.create_group('Work Lunch', bob.id)

    # Add members to groups
    group_repo.add_group_member(friends_group.id, alice, is_group_admin=True)
    group_repo.add_group_member(friends_group.id, bob)
    group_repo.add_group_member(friends_group.id, carol)
    group_repo.add_group_member(friends_group.id, test_user, is_group_admin=True)
    # David is not in any group (for testing merge of non-member)
    group_repo.add_group_member(friends_group.id, emily, is_group_admin=True)  # Group admin
    group_repo.add_group_member(friends_group.id, frank)  # Regular member with run participation

    group_repo.add_group_member(work_group.id, bob, is_group_admin=True)
    group_repo.add_group_member(work_group.id, carol)

    # Create test stores
    costco = store_repo.create_store('Test Costco')
    sams = store_repo.create_store("Test Sam's Club")

    # Create test products (store-agnostic)
    olive_oil = product_repo.create_product('Test Olive Oil', brand='Kirkland', unit='L')
    quinoa = product_repo.create_product('Test Quinoa', brand='Organic', unit='kg')
    detergent = product_repo.create_product('Test Detergent', brand='Tide', unit='L')
    paper_towels = product_repo.create_product(
        'Kirkland Paper Towels 12-pack', brand='Kirkland', unit='pack'
    )
    rotisserie_chicken = product_repo.create_product('Rotisserie Chicken', unit='each')
    almond_butter = product_repo.create_product('Kirkland Almond Butter', brand='Kirkland', unit='kg')
    frozen_berries = product_repo.create_product('Organic Frozen Berry Mix', brand='Organic', unit='kg')
    toilet_paper = product_repo.create_product('Charmin Ultra Soft 24-pack', brand='Charmin', unit='pack')
    coffee_beans = product_repo.create_product('Kirkland Colombian Coffee', brand='Kirkland', unit='kg')
    laundry_pods = product_repo.create_product('Tide Pods 81-count', brand='Tide', unit='pack')
    ground_beef = product_repo.create_product('93/7 Ground Beef 3lbs', unit='kg')
    bananas = product_repo.create_product('Organic Bananas 3lbs', brand='Organic', unit='kg')
    cheese_sticks = product_repo.create_product('String Cheese 48-pack', unit='pack')

    # Create product availabilities (link products to stores with prices)
    # Olive Oil - multiple prices from 2 days ago (for confirmed run at Costco)
    availability = product_repo.create_product_availability(olive_oil.id, costco.id, 24.99, 'aisle 12')
    availability.created_at = datetime.now(UTC) - timedelta(days=2)
    availability.updated_at = datetime.now(UTC) - timedelta(days=2)

    availability = product_repo.create_product_availability(olive_oil.id, costco.id, 23.99, 'end cap display')
    availability.created_at = datetime.now(UTC) - timedelta(days=2)
    availability.updated_at = datetime.now(UTC) - timedelta(days=2)

    # Quinoa - one price from yesterday (for confirmed run at Costco)
    availability = product_repo.create_product_availability(quinoa.id, costco.id, 18.99, 'organic section')
    availability.created_at = datetime.now(UTC) - timedelta(days=1)
    availability.updated_at = datetime.now(UTC) - timedelta(days=1)

    # Paper Towels - prices from 5 days ago (for confirmed run at Costco)
    availability = product_repo.create_product_availability(paper_towels.id, costco.id, 19.99, 'household')
    availability.created_at = datetime.now(UTC) - timedelta(days=5)
    availability.updated_at = datetime.now(UTC) - timedelta(days=5)

    availability = product_repo.create_product_availability(paper_towels.id, costco.id, 21.49, 'regular price')
    availability.created_at = datetime.now(UTC) - timedelta(days=5)
    availability.updated_at = datetime.now(UTC) - timedelta(days=5)

    # Other Costco products
    availability = product_repo.create_product_availability(rotisserie_chicken.id, costco.id, 4.99, 'deli section')
    availability.created_at = datetime.now(UTC) - timedelta(days=1)
    availability.updated_at = datetime.now(UTC) - timedelta(days=1)

    availability = product_repo.create_product_availability(almond_butter.id, costco.id, 9.99, '')
    availability.created_at = datetime.now(UTC) - timedelta(days=3)
    availability.updated_at = datetime.now(UTC) - timedelta(days=3)

    availability = product_repo.create_product_availability(almond_butter.id, costco.id, 10.49, 'clearance')
    availability.created_at = datetime.now(UTC) - timedelta(days=3)
    availability.updated_at = datetime.now(UTC) - timedelta(days=3)

    # Older observations (week ago)
    availability = product_repo.create_product_availability(frozen_berries.id, costco.id, 12.99, '')
    availability.created_at = datetime.now(UTC) - timedelta(days=7)
    availability.updated_at = datetime.now(UTC) - timedelta(days=7)

    availability = product_repo.create_product_availability(toilet_paper.id, costco.id, 22.99, '')
    availability.created_at = datetime.now(UTC) - timedelta(days=7)
    availability.updated_at = datetime.now(UTC) - timedelta(days=7)

    availability = product_repo.create_product_availability(coffee_beans.id, costco.id, 14.99, '')
    availability.created_at = datetime.now(UTC) - timedelta(days=7)
    availability.updated_at = datetime.now(UTC) - timedelta(days=7)

    # Sam's Club - varied dates
    availability = product_repo.create_product_availability(detergent.id, sams.id, 16.98, '')
    # days_ago=0, no backdating needed

    availability = product_repo.create_product_availability(detergent.id, sams.id, 15.98, 'on sale')
    # days_ago=0, no backdating needed

    availability = product_repo.create_product_availability(laundry_pods.id, sams.id, 18.98, '')
    availability.created_at = datetime.now(UTC) - timedelta(days=2)
    availability.updated_at = datetime.now(UTC) - timedelta(days=2)

    availability = product_repo.create_product_availability(ground_beef.id, sams.id, 16.48, '')
    availability.created_at = datetime.now(UTC) - timedelta(days=2)
    availability.updated_at = datetime.now(UTC) - timedelta(days=2)

    availability = product_repo.create_product_availability(ground_beef.id, sams.id, 17.98, 'higher price today')
    availability.created_at = datetime.now(UTC) - timedelta(days=2)
    availability.updated_at = datetime.now(UTC) - timedelta(days=2)

    availability = product_repo.create_product_availability(bananas.id, sams.id, 4.98, '')
    availability.created_at = datetime.now(UTC) - timedelta(days=5)
    availability.updated_at = datetime.now(UTC) - timedelta(days=5)

    availability = product_repo.create_product_availability(cheese_sticks.id, sams.id, 8.98, '')
    availability.created_at = datetime.now(UTC) - timedelta(days=5)
    availability.updated_at = datetime.now(UTC) - timedelta(days=5)

    # Create test runs - one for each state with test user as leader
    run_planning = run_repo.create_run(friends_group.id, costco.id, test_user.id)
    run_planning.state = RunState.PLANNING
    run_planning.planning_at = datetime.now(UTC) - timedelta(days=7)

    run_active = run_repo.create_run(friends_group.id, sams.id, test_user.id)
    run_active.state = RunState.ACTIVE
    run_active.planning_at = datetime.now(UTC) - timedelta(days=5)
    run_active.active_at = datetime.now(UTC) - timedelta(days=5)

    run_confirmed = run_repo.create_run(friends_group.id, costco.id, test_user.id)
    run_confirmed.state = RunState.CONFIRMED
    run_confirmed.planning_at = datetime.now(UTC) - timedelta(days=3)
    run_confirmed.active_at = datetime.now(UTC) - timedelta(days=3)
    run_confirmed.confirmed_at = datetime.now(UTC) - timedelta(days=3)

    run_shopping = run_repo.create_run(friends_group.id, sams.id, test_user.id)
    run_shopping.state = RunState.SHOPPING
    run_shopping.planning_at = datetime.now(UTC) - timedelta(days=2)
    run_shopping.active_at = datetime.now(UTC) - timedelta(days=2)
    run_shopping.confirmed_at = datetime.now(UTC) - timedelta(days=2)
    run_shopping.shopping_at = datetime.now(UTC) - timedelta(days=2)

    run_adjusting = run_repo.create_run(friends_group.id, costco.id, test_user.id)
    run_adjusting.state = RunState.ADJUSTING
    run_adjusting.planning_at = datetime.now(UTC) - timedelta(days=1.5)
    run_adjusting.active_at = datetime.now(UTC) - timedelta(days=1.5)
    run_adjusting.confirmed_at = datetime.now(UTC) - timedelta(days=1.5)
    run_adjusting.shopping_at = datetime.now(UTC) - timedelta(days=1.5)
    run_adjusting.adjusting_at = datetime.now(UTC) - timedelta(days=1.5)

    run_distributing = run_repo.create_run(friends_group.id, costco.id, test_user.id)
    run_distributing.state = RunState.DISTRIBUTING
    run_distributing.planning_at = datetime.now(UTC) - timedelta(days=1)
    run_distributing.active_at = datetime.now(UTC) - timedelta(days=1)
    run_distributing.confirmed_at = datetime.now(UTC) - timedelta(days=1)
    run_distributing.shopping_at = datetime.now(UTC) - timedelta(days=1)
    run_distributing.adjusting_at = datetime.now(UTC) - timedelta(days=1)
    run_distributing.distributing_at = datetime.now(UTC) - timedelta(days=1)

    run_completed = run_repo.create_run(friends_group.id, sams.id, test_user.id)
    run_completed.state = RunState.COMPLETED
    run_completed.planning_at = datetime.now(UTC) - timedelta(days=14)
    run_completed.active_at = datetime.now(UTC) - timedelta(days=14)
    run_completed.confirmed_at = datetime.now(UTC) - timedelta(days=14)
    run_completed.shopping_at = datetime.now(UTC) - timedelta(days=14)
    run_completed.adjusting_at = datetime.now(UTC) - timedelta(days=14)
    run_completed.distributing_at = datetime.now(UTC) - timedelta(days=14)
    run_completed.completed_at = datetime.now(UTC) - timedelta(days=14)

    # Add more completed runs with different dates for better price history
    run_completed_2 = run_repo.create_run(friends_group.id, costco.id, test_user.id)
    run_completed_2.state = RunState.COMPLETED
    run_completed_2.planning_at = datetime.now(UTC) - timedelta(days=30)
    run_completed_2.active_at = datetime.now(UTC) - timedelta(days=30)
    run_completed_2.confirmed_at = datetime.now(UTC) - timedelta(days=30)
    run_completed_2.shopping_at = datetime.now(UTC) - timedelta(days=30)
    run_completed_2.adjusting_at = datetime.now(UTC) - timedelta(days=30)
    run_completed_2.distributing_at = datetime.now(UTC) - timedelta(days=30)
    run_completed_2.completed_at = datetime.now(UTC) - timedelta(days=30)

    run_completed_3 = run_repo.create_run(friends_group.id, sams.id, alice.id)
    run_completed_3.state = RunState.COMPLETED
    run_completed_3.planning_at = datetime.now(UTC) - timedelta(days=45)
    run_completed_3.active_at = datetime.now(UTC) - timedelta(days=45)
    run_completed_3.confirmed_at = datetime.now(UTC) - timedelta(days=45)
    run_completed_3.shopping_at = datetime.now(UTC) - timedelta(days=45)
    run_completed_3.adjusting_at = datetime.now(UTC) - timedelta(days=45)
    run_completed_3.distributing_at = datetime.now(UTC) - timedelta(days=45)
    run_completed_3.completed_at = datetime.now(UTC) - timedelta(days=45)

    run_completed_4 = run_repo.create_run(friends_group.id, costco.id, bob.id)
    run_completed_4.state = RunState.COMPLETED
    run_completed_4.planning_at = datetime.now(UTC) - timedelta(days=60)
    run_completed_4.active_at = datetime.now(UTC) - timedelta(days=60)
    run_completed_4.confirmed_at = datetime.now(UTC) - timedelta(days=60)
    run_completed_4.shopping_at = datetime.now(UTC) - timedelta(days=60)
    run_completed_4.adjusting_at = datetime.now(UTC) - timedelta(days=60)
    run_completed_4.distributing_at = datetime.now(UTC) - timedelta(days=60)
    run_completed_4.completed_at = datetime.now(UTC) - timedelta(days=60)

    run_completed_5 = run_repo.create_run(work_group.id, sams.id, bob.id)
    run_completed_5.state = RunState.COMPLETED
    run_completed_5.planning_at = datetime.now(UTC) - timedelta(days=75)
    run_completed_5.active_at = datetime.now(UTC) - timedelta(days=75)
    run_completed_5.confirmed_at = datetime.now(UTC) - timedelta(days=75)
    run_completed_5.shopping_at = datetime.now(UTC) - timedelta(days=75)
    run_completed_5.adjusting_at = datetime.now(UTC) - timedelta(days=75)
    run_completed_5.distributing_at = datetime.now(UTC) - timedelta(days=75)
    run_completed_5.completed_at = datetime.now(UTC) - timedelta(days=75)

    # Planning run - test user is leader (no other participants yet)
    # (no additional participants to create for planning run)

    # Active run - test user is leader, others have bid
    test_active_p = run_repo.get_participation(test_user.id, run_active.id)
    alice_active_p = run_repo.create_participation(alice.id, run_active.id, is_leader=False)
    bob_active_p = run_repo.create_participation(bob.id, run_active.id, is_leader=False)
    carol_active_p = run_repo.create_participation(carol.id, run_active.id, is_leader=False)

    # Detergent - multiple users want it
    bid_repo.create_or_update_bid(test_active_p.id, detergent.id, 2, False)
    bid_repo.create_or_update_bid(alice_active_p.id, detergent.id, 1, False)
    bid_repo.create_or_update_bid(bob_active_p.id, detergent.id, 1, False)

    # Laundry Pods - just bob
    bid_repo.create_or_update_bid(bob_active_p.id, laundry_pods.id, 2, False)

    # Ground Beef - test user and carol
    bid_repo.create_or_update_bid(test_active_p.id, ground_beef.id, 1, False)
    bid_repo.create_or_update_bid(carol_active_p.id, ground_beef.id, 2, False)

    # Bananas - interested only from alice
    bid_repo.create_or_update_bid(alice_active_p.id, bananas.id, 0, True)

    # Confirmed run - test user is leader, all are ready
    test_confirmed_p = run_repo.get_participation(test_user.id, run_confirmed.id)
    test_confirmed_p.is_ready = True
    alice_confirmed_p = run_repo.create_participation(alice.id, run_confirmed.id, is_leader=False)
    alice_confirmed_p.is_ready = True
    bob_confirmed_p = run_repo.create_participation(bob.id, run_confirmed.id, is_leader=False)
    bob_confirmed_p.is_ready = True
    carol_confirmed_p = run_repo.create_participation(carol.id, run_confirmed.id, is_leader=False)
    carol_confirmed_p.is_ready = True

    # All users want olive oil
    bid_repo.create_or_update_bid(test_confirmed_p.id, olive_oil.id, 1, False)
    bid_repo.create_or_update_bid(alice_confirmed_p.id, olive_oil.id, 1, False)
    bid_repo.create_or_update_bid(bob_confirmed_p.id, olive_oil.id, 2, False)
    bid_repo.create_or_update_bid(carol_confirmed_p.id, olive_oil.id, 1, False)

    # Quinoa - just alice and carol
    bid_repo.create_or_update_bid(alice_confirmed_p.id, quinoa.id, 1, False)
    bid_repo.create_or_update_bid(carol_confirmed_p.id, quinoa.id, 1, False)

    # Paper Towels - everyone interested
    bid_repo.create_or_update_bid(test_confirmed_p.id, paper_towels.id, 1, False)
    bid_repo.create_or_update_bid(alice_confirmed_p.id, paper_towels.id, 2, False)
    bid_repo.create_or_update_bid(bob_confirmed_p.id, paper_towels.id, 1, False)
    bid_repo.create_or_update_bid(carol_confirmed_p.id, paper_towels.id, 0, True)  # interested only

    # Shopping run - test user is leader, has shopping list items
    test_shopping_p = run_repo.get_participation(test_user.id, run_shopping.id)
    test_shopping_p.is_ready = True
    alice_shopping_p = run_repo.create_participation(alice.id, run_shopping.id, is_leader=False)
    alice_shopping_p.is_ready = True
    bob_shopping_p = run_repo.create_participation(bob.id, run_shopping.id, is_leader=False)
    bob_shopping_p.is_ready = True

    # Create bids for shopping run
    bid_repo.create_or_update_bid(test_shopping_p.id, detergent.id, 1, False)
    bid_repo.create_or_update_bid(alice_shopping_p.id, laundry_pods.id, 1, False)
    bid_repo.create_or_update_bid(bob_shopping_p.id, ground_beef.id, 2, False)

    # Shopping list items for shopping run
    shopping_item1 = shopping_repo.create_shopping_list_item(run_shopping.id, detergent.id, 1)
    shopping_item1.is_purchased = False
    shopping_item1.purchase_order = 1

    shopping_item2 = shopping_repo.create_shopping_list_item(run_shopping.id, laundry_pods.id, 1)
    shopping_item2.is_purchased = False
    shopping_item2.purchase_order = 2

    shopping_item3 = shopping_repo.create_shopping_list_item(run_shopping.id, ground_beef.id, 2)
    shopping_item3.is_purchased = False
    shopping_item3.purchase_order = 3

    # Adjusting run - quantities fell short, some users need to adjust bids
    test_adjusting_p = run_repo.get_participation(test_user.id, run_adjusting.id)
    test_adjusting_p.is_ready = True
    alice_adjusting_p = run_repo.create_participation(alice.id, run_adjusting.id, is_leader=False)
    alice_adjusting_p.is_ready = True
    bob_adjusting_p = run_repo.create_participation(bob.id, run_adjusting.id, is_leader=False)
    bob_adjusting_p.is_ready = True
    carol_adjusting_p = run_repo.create_participation(carol.id, run_adjusting.id, is_leader=False)
    carol_adjusting_p.is_ready = True

    # Bids for adjusting run
    bid_repo.create_or_update_bid(test_adjusting_p.id, almond_butter.id, 2, False)
    bid_repo.create_or_update_bid(alice_adjusting_p.id, almond_butter.id, 1, False)
    bid_repo.create_or_update_bid(bob_adjusting_p.id, almond_butter.id, 1, False)

    bid_repo.create_or_update_bid(test_adjusting_p.id, frozen_berries.id, 1, False)
    bid_repo.create_or_update_bid(carol_adjusting_p.id, frozen_berries.id, 2, False)

    # Toilet Paper - requested 3 but purchased 4 (only sold in 4-packs)
    bid_repo.create_or_update_bid(test_adjusting_p.id, toilet_paper.id, 1, False)
    bid_repo.create_or_update_bid(alice_adjusting_p.id, toilet_paper.id, 1, False)
    bid_repo.create_or_update_bid(bob_adjusting_p.id, toilet_paper.id, 1, False)

    # Coffee Beans - surplus without leader (requested 2, purchased 3 - only sold in 3-packs)
    bid_repo.create_or_update_bid(alice_adjusting_p.id, coffee_beans.id, 1, False)
    bid_repo.create_or_update_bid(bob_adjusting_p.id, coffee_beans.id, 1, False)

    # Rotisserie Chicken - NOT purchased (out of stock)
    bid_repo.create_or_update_bid(test_adjusting_p.id, rotisserie_chicken.id, 2, False)
    bid_repo.create_or_update_bid(carol_adjusting_p.id, rotisserie_chicken.id, 1, False)

    # Paper Towels - NOT purchased (decided not to buy)
    bid_repo.create_or_update_bid(alice_adjusting_p.id, paper_towels.id, 1, False)
    bid_repo.create_or_update_bid(bob_adjusting_p.id, paper_towels.id, 1, False)

    # Olive Oil - CORRECTLY purchased (requested 3, purchased 3) - no adjustment needed
    bid_repo.create_or_update_bid(test_adjusting_p.id, olive_oil.id, 1, False)
    bid_repo.create_or_update_bid(alice_adjusting_p.id, olive_oil.id, 1, False)
    bid_repo.create_or_update_bid(carol_adjusting_p.id, olive_oil.id, 1, False)

    # Quinoa - CORRECTLY purchased (requested 2, purchased 2) - no adjustment needed
    bid_repo.create_or_update_bid(bob_adjusting_p.id, quinoa.id, 1, False)
    bid_repo.create_or_update_bid(carol_adjusting_p.id, quinoa.id, 1, False)

    # Shopping list items for adjusting run
    # Almond Butter - shortage (requested 4, purchased 3)
    shopping_item4 = shopping_repo.create_shopping_list_item(
        run_adjusting.id, almond_butter.id, 4
    )  # 2 + 1 + 1
    shopping_item4.is_purchased = True
    shopping_item4.purchased_price_per_unit = 9.99
    shopping_item4.purchased_quantity = 3
    shopping_item4.purchase_order = 1

    # Frozen Berries - shortage (requested 3, purchased 2)
    shopping_item5 = shopping_repo.create_shopping_list_item(
        run_adjusting.id, frozen_berries.id, 3
    )  # 1 + 2
    shopping_item5.is_purchased = True
    shopping_item5.purchased_price_per_unit = 12.99
    shopping_item5.purchased_quantity = 2
    shopping_item5.purchase_order = 2

    # Toilet Paper - surplus (requested 3, purchased 4 - only sold in 4-packs)
    shopping_item_tp = shopping_repo.create_shopping_list_item(
        run_adjusting.id, toilet_paper.id, 3
    )  # 1 + 1 + 1
    shopping_item_tp.is_purchased = True
    shopping_item_tp.purchased_price_per_unit = 22.99
    shopping_item_tp.purchased_quantity = 4
    shopping_item_tp.purchase_order = 3

    # Coffee Beans - surplus without leader (requested 2, purchased 3 - only sold in 3-packs)
    shopping_item_coffee = shopping_repo.create_shopping_list_item(
        run_adjusting.id, coffee_beans.id, 2
    )  # 1 + 1
    shopping_item_coffee.is_purchased = True
    shopping_item_coffee.purchased_price_per_unit = 14.99
    shopping_item_coffee.purchased_quantity = 3
    shopping_item_coffee.purchase_order = 4

    # Rotisserie Chicken - NOT purchased (out of stock)
    shopping_item_chicken = shopping_repo.create_shopping_list_item(
        run_adjusting.id, rotisserie_chicken.id, 3
    )  # 2 + 1
    shopping_item_chicken.is_purchased = False
    shopping_item_chicken.purchased_quantity = None
    shopping_item_chicken.purchase_order = None

    # Paper Towels - NOT purchased (decided not to buy)
    shopping_item_pt_adj = shopping_repo.create_shopping_list_item(
        run_adjusting.id, paper_towels.id, 2
    )  # 1 + 1
    shopping_item_pt_adj.is_purchased = False
    shopping_item_pt_adj.purchased_quantity = None
    shopping_item_pt_adj.purchase_order = None

    # Olive Oil - CORRECTLY purchased (requested 3, purchased 3) - no adjustment needed
    shopping_item_oil = shopping_repo.create_shopping_list_item(
        run_adjusting.id, olive_oil.id, 3
    )  # 1 + 1 + 1
    shopping_item_oil.is_purchased = True
    shopping_item_oil.purchased_price_per_unit = 23.99
    shopping_item_oil.purchased_quantity = 3
    shopping_item_oil.purchase_order = 5

    # Quinoa - CORRECTLY purchased (requested 2, purchased 2) - no adjustment needed
    shopping_item_quinoa_adj = shopping_repo.create_shopping_list_item(
        run_adjusting.id, quinoa.id, 2
    )  # 1 + 1
    shopping_item_quinoa_adj.is_purchased = True
    shopping_item_quinoa_adj.purchased_price_per_unit = 18.99
    shopping_item_quinoa_adj.purchased_quantity = 2
    shopping_item_quinoa_adj.purchase_order = 6

    # Distributing run - items purchased, being distributed
    test_distributing_p = run_repo.get_participation(test_user.id, run_distributing.id)
    test_distributing_p.is_ready = True
    alice_distributing_p = run_repo.create_participation(alice.id, run_distributing.id, is_leader=False)
    alice_distributing_p.is_ready = True
    bob_distributing_p = run_repo.create_participation(bob.id, run_distributing.id, is_leader=False)
    bob_distributing_p.is_ready = True

    # Bids with distributed quantities
    bid6 = bid_repo.create_or_update_bid(test_distributing_p.id, rotisserie_chicken.id, 2, False)
    bid6.distributed_quantity = 2
    bid6.distributed_price_per_unit = 4.99

    bid7 = bid_repo.create_or_update_bid(alice_distributing_p.id, rotisserie_chicken.id, 1, False)
    bid7.distributed_quantity = 1
    bid7.distributed_price_per_unit = 4.99

    bid8 = bid_repo.create_or_update_bid(bob_distributing_p.id, toilet_paper.id, 1, False)
    bid8.distributed_quantity = 1
    bid8.distributed_price_per_unit = 22.99

    bid9 = bid_repo.create_or_update_bid(test_distributing_p.id, coffee_beans.id, 2, False)
    bid9.distributed_quantity = 2
    bid9.distributed_price_per_unit = 14.99

    # Shopping list items
    shopping_item6 = shopping_repo.create_shopping_list_item(
        run_distributing.id, rotisserie_chicken.id, 3
    )  # 2 + 1
    shopping_item6.is_purchased = True
    shopping_item6.purchased_price_per_unit = 4.99
    shopping_item6.purchased_quantity = 3
    shopping_item6.purchase_order = 1

    shopping_item7 = shopping_repo.create_shopping_list_item(run_distributing.id, toilet_paper.id, 1)
    shopping_item7.is_purchased = True
    shopping_item7.purchased_price_per_unit = 22.99
    shopping_item7.purchased_quantity = 1
    shopping_item7.purchase_order = 2

    shopping_item8 = shopping_repo.create_shopping_list_item(run_distributing.id, coffee_beans.id, 2)
    shopping_item8.is_purchased = True
    shopping_item8.purchased_price_per_unit = 14.99
    shopping_item8.purchased_quantity = 2
    shopping_item8.purchase_order = 3

    # Distribution records for distributing run
    alice_distributing_p.picked_up_at = None
    bob_distributing_p.picked_up_at = None

    # Completed run - all done
    test_completed_p = run_repo.get_participation(test_user.id, run_completed.id)
    test_completed_p.is_ready = True
    test_completed_p.picked_up_at = datetime.now(UTC) - timedelta(days=13)

    alice_completed_p = run_repo.create_participation(alice.id, run_completed.id, is_leader=False)
    alice_completed_p.is_ready = True
    alice_completed_p.picked_up_at = datetime.now(UTC) - timedelta(days=13)

    # Bids for completed run
    bid10 = bid_repo.create_or_update_bid(test_completed_p.id, detergent.id, 1, False)
    bid10.distributed_quantity = 1
    bid10.distributed_price_per_unit = 16.98

    bid11 = bid_repo.create_or_update_bid(alice_completed_p.id, laundry_pods.id, 1, False)
    bid11.distributed_quantity = 1
    bid11.distributed_price_per_unit = 18.98

    # Shopping list items
    shopping_item9 = shopping_repo.create_shopping_list_item(run_completed.id, detergent.id, 1)
    shopping_item9.is_purchased = True
    shopping_item9.purchased_price_per_unit = 16.98
    shopping_item9.purchased_quantity = 1
    shopping_item9.purchase_order = 1

    shopping_item10 = shopping_repo.create_shopping_list_item(run_completed.id, laundry_pods.id, 1)
    shopping_item10.is_purchased = True
    shopping_item10.purchased_price_per_unit = 18.98
    shopping_item10.purchased_quantity = 1
    shopping_item10.purchase_order = 2

    # Additional completed runs for price history
    # run_completed_2 (30 days ago)
    test_completed_2_p = run_repo.get_participation(test_user.id, run_completed_2.id)
    test_completed_2_p.is_ready = True
    test_completed_2_p.picked_up_at = datetime.now(UTC) - timedelta(days=29)

    bob_completed_2_p = run_repo.create_participation(bob.id, run_completed_2.id, is_leader=False)
    bob_completed_2_p.is_ready = True
    bob_completed_2_p.picked_up_at = datetime.now(UTC) - timedelta(days=29)

    # Add Frank to this completed run (for testing user merge)
    frank_completed_2_p = run_repo.create_participation(frank.id, run_completed_2.id, is_leader=False)
    frank_completed_2_p.is_ready = True
    frank_completed_2_p.picked_up_at = datetime.now(UTC) - timedelta(days=29)

    bid12 = bid_repo.create_or_update_bid(test_completed_2_p.id, olive_oil.id, 1, False)
    bid12.distributed_quantity = 1
    bid12.distributed_price_per_unit = 23.99

    bid13 = bid_repo.create_or_update_bid(bob_completed_2_p.id, paper_towels.id, 1, False)
    bid13.distributed_quantity = 1
    bid13.distributed_price_per_unit = 19.99

    bid_frank = bid_repo.create_or_update_bid(frank_completed_2_p.id, quinoa.id, 1, False)
    bid_frank.distributed_quantity = 1
    bid_frank.distributed_price_per_unit = 18.99

    shopping_item11 = shopping_repo.create_shopping_list_item(run_completed_2.id, olive_oil.id, 1)
    shopping_item11.is_purchased = True
    shopping_item11.purchased_price_per_unit = 23.99
    shopping_item11.purchased_quantity = 1
    shopping_item11.purchase_order = 1

    shopping_item12 = shopping_repo.create_shopping_list_item(run_completed_2.id, paper_towels.id, 1)
    shopping_item12.is_purchased = True
    shopping_item12.purchased_price_per_unit = 19.99
    shopping_item12.purchased_quantity = 1
    shopping_item12.purchase_order = 2

    shopping_item_quinoa = shopping_repo.create_shopping_list_item(run_completed_2.id, quinoa.id, 1)
    shopping_item_quinoa.is_purchased = True
    shopping_item_quinoa.purchased_price_per_unit = 18.99
    shopping_item_quinoa.purchased_quantity = 1
    shopping_item_quinoa.purchase_order = 3

    # run_completed_3 (45 days ago) - alice is leader
    alice_completed_3_p = run_repo.get_participation(alice.id, run_completed_3.id)
    alice_completed_3_p.is_ready = True
    alice_completed_3_p.picked_up_at = datetime.now(UTC) - timedelta(days=44)

    carol_completed_3_p = run_repo.create_participation(carol.id, run_completed_3.id, is_leader=False)
    carol_completed_3_p.is_ready = True
    carol_completed_3_p.picked_up_at = datetime.now(UTC) - timedelta(days=44)

    bid14 = bid_repo.create_or_update_bid(alice_completed_3_p.id, detergent.id, 2, False)
    bid14.distributed_quantity = 2
    bid14.distributed_price_per_unit = 15.98

    shopping_item13 = shopping_repo.create_shopping_list_item(run_completed_3.id, detergent.id, 2)
    shopping_item13.is_purchased = True
    shopping_item13.purchased_price_per_unit = 15.98
    shopping_item13.purchased_quantity = 2
    shopping_item13.purchase_order = 1

    # run_completed_4 (60 days ago) - bob is leader
    bob_completed_4_p = run_repo.get_participation(bob.id, run_completed_4.id)
    bob_completed_4_p.is_ready = True
    bob_completed_4_p.picked_up_at = datetime.now(UTC) - timedelta(days=59)

    shopping_item14 = shopping_repo.create_shopping_list_item(run_completed_4.id, olive_oil.id, 1)
    shopping_item14.is_purchased = True
    shopping_item14.purchased_price_per_unit = 24.99
    shopping_item14.purchased_quantity = 1
    shopping_item14.purchase_order = 1

    bid15 = bid_repo.create_or_update_bid(bob_completed_4_p.id, olive_oil.id, 1, False)
    bid15.distributed_quantity = 1
    bid15.distributed_price_per_unit = 24.99

    # run_completed_5 (75 days ago) - bob is leader, work group
    bob_completed_5_p = run_repo.get_participation(bob.id, run_completed_5.id)
    bob_completed_5_p.is_ready = True
    bob_completed_5_p.picked_up_at = datetime.now(UTC) - timedelta(days=74)

    carol_completed_5_p = run_repo.create_participation(carol.id, run_completed_5.id, is_leader=False)
    carol_completed_5_p.is_ready = True
    carol_completed_5_p.picked_up_at = datetime.now(UTC) - timedelta(days=74)

    bid16 = bid_repo.create_or_update_bid(bob_completed_5_p.id, ground_beef.id, 1, False)
    bid16.distributed_quantity = 1
    bid16.distributed_price_per_unit = 16.48

    shopping_item15 = shopping_repo.create_shopping_list_item(run_completed_5.id, ground_beef.id, 1)
    shopping_item15.is_purchased = True
    shopping_item15.purchased_price_per_unit = 16.48
    shopping_item15.purchased_quantity = 1
    shopping_item15.purchase_order = 1
