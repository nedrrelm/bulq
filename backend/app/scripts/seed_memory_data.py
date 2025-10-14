"""Seed data for in-memory repository mode."""


def seed_memory_repository(repo):
    """Create test data for memory repository.

    Args:
        repo: MemoryRepository instance to populate
    """
    # Create test users
    alice = repo.create_user('Alice Johnson', 'alice@test.com', 'hashed_password')
    bob = repo.create_user('Bob Smith', 'bob@test.com', 'hashed_password')
    carol = repo.create_user('Carol Davis', 'carol@test.com', 'hashed_password')
    test_user = repo.create_user('Test User', 'test@example.com', 'hashed_password')
    test_user.is_admin = True

    # Create test groups
    friends_group = repo.create_group('Test Friends', alice.id)
    work_group = repo.create_group('Work Lunch', bob.id)

    # Add members to groups
    repo.add_group_member(friends_group.id, alice, is_group_admin=True)
    repo.add_group_member(friends_group.id, bob)
    repo.add_group_member(friends_group.id, carol)
    repo.add_group_member(friends_group.id, test_user, is_group_admin=True)

    repo.add_group_member(work_group.id, bob, is_group_admin=True)
    repo.add_group_member(work_group.id, carol)

    # Create test stores
    costco = repo._create_store('Test Costco')
    sams = repo._create_store("Test Sam's Club")

    # Create test products (store-agnostic)
    olive_oil = repo._create_product('Test Olive Oil', brand='Kirkland')
    quinoa = repo._create_product('Test Quinoa', brand='Organic')
    detergent = repo._create_product('Test Detergent', brand='Tide')
    paper_towels = repo._create_product('Kirkland Paper Towels 12-pack', brand='Kirkland')
    rotisserie_chicken = repo._create_product('Rotisserie Chicken')
    almond_butter = repo._create_product('Kirkland Almond Butter', brand='Kirkland')
    frozen_berries = repo._create_product('Organic Frozen Berry Mix', brand='Organic')
    toilet_paper = repo._create_product('Charmin Ultra Soft 24-pack', brand='Charmin')
    coffee_beans = repo._create_product('Kirkland Colombian Coffee', brand='Kirkland')
    laundry_pods = repo._create_product('Tide Pods 81-count', brand='Tide')
    ground_beef = repo._create_product('93/7 Ground Beef 3lbs')
    bananas = repo._create_product('Organic Bananas 3lbs', brand='Organic')
    cheese_sticks = repo._create_product('String Cheese 48-pack')

    # Create product availabilities (link products to stores with prices)
    # Olive Oil - multiple prices from 2 days ago (for confirmed run at Costco)
    repo._create_product_availability(olive_oil.id, costco.id, 24.99, 'aisle 12', days_ago=2)
    repo._create_product_availability(olive_oil.id, costco.id, 23.99, 'end cap display', days_ago=2)

    # Quinoa - one price from yesterday (for confirmed run at Costco)
    repo._create_product_availability(quinoa.id, costco.id, 18.99, 'organic section', days_ago=1)

    # Paper Towels - prices from 5 days ago (for confirmed run at Costco)
    repo._create_product_availability(paper_towels.id, costco.id, 19.99, 'household', days_ago=5)
    repo._create_product_availability(paper_towels.id, costco.id, 21.49, 'regular price', days_ago=5)

    # Other Costco products
    repo._create_product_availability(rotisserie_chicken.id, costco.id, 4.99, 'deli section', days_ago=1)
    repo._create_product_availability(almond_butter.id, costco.id, 9.99, '', days_ago=3)
    repo._create_product_availability(almond_butter.id, costco.id, 10.49, 'clearance', days_ago=3)

    # Older observations (week ago)
    repo._create_product_availability(frozen_berries.id, costco.id, 12.99, '', days_ago=7)
    repo._create_product_availability(toilet_paper.id, costco.id, 22.99, '', days_ago=7)
    repo._create_product_availability(coffee_beans.id, costco.id, 14.99, '', days_ago=7)

    # Sam's Club - varied dates
    repo._create_product_availability(detergent.id, sams.id, 16.98, '', days_ago=0)
    repo._create_product_availability(detergent.id, sams.id, 15.98, 'on sale', days_ago=0)
    repo._create_product_availability(laundry_pods.id, sams.id, 18.98, '', days_ago=2)
    repo._create_product_availability(ground_beef.id, sams.id, 16.48, '', days_ago=2)
    repo._create_product_availability(ground_beef.id, sams.id, 17.98, 'higher price today', days_ago=2)
    repo._create_product_availability(bananas.id, sams.id, 4.98, '', days_ago=5)
    repo._create_product_availability(cheese_sticks.id, sams.id, 8.98, '', days_ago=5)

    # Create test runs - one for each state with test user as leader
    run_planning = repo._create_run(friends_group.id, costco.id, 'planning', test_user.id, days_ago=7)
    run_active = repo._create_run(friends_group.id, sams.id, 'active', test_user.id, days_ago=5)
    run_confirmed = repo._create_run(friends_group.id, costco.id, 'confirmed', test_user.id, days_ago=3)
    run_shopping = repo._create_run(friends_group.id, sams.id, 'shopping', test_user.id, days_ago=2)
    run_adjusting = repo._create_run(friends_group.id, costco.id, 'adjusting', test_user.id, days_ago=1.5)
    run_distributing = repo._create_run(friends_group.id, costco.id, 'distributing', test_user.id, days_ago=1)
    run_completed = repo._create_run(friends_group.id, sams.id, 'completed', test_user.id, days_ago=14)

    # Add more completed runs with different dates for better price history
    run_completed_2 = repo._create_run(friends_group.id, costco.id, 'completed', test_user.id, days_ago=30)
    run_completed_3 = repo._create_run(friends_group.id, sams.id, 'completed', alice.id, days_ago=45)
    run_completed_4 = repo._create_run(friends_group.id, costco.id, 'completed', bob.id, days_ago=60)
    run_completed_5 = repo._create_run(work_group.id, sams.id, 'completed', bob.id, days_ago=75)

    # Planning run - test user is leader (no other participants yet)
    test_planning_p = next(
        (p for p in repo._participations.values() if p.user_id == test_user.id and p.run_id == run_planning.id), None
    )

    # Active run - test user is leader, others have bid
    test_active_p = next(
        (p for p in repo._participations.values() if p.user_id == test_user.id and p.run_id == run_active.id), None
    )
    alice_active_p = repo._create_participation(alice.id, run_active.id, is_leader=False)
    bob_active_p = repo._create_participation(bob.id, run_active.id, is_leader=False)
    carol_active_p = repo._create_participation(carol.id, run_active.id, is_leader=False)

    # Detergent - multiple users want it
    repo._create_bid(test_active_p.id, detergent.id, 2, False)
    repo._create_bid(alice_active_p.id, detergent.id, 1, False)
    repo._create_bid(bob_active_p.id, detergent.id, 1, False)

    # Laundry Pods - just bob
    repo._create_bid(bob_active_p.id, laundry_pods.id, 2, False)

    # Ground Beef - test user and carol
    repo._create_bid(test_active_p.id, ground_beef.id, 1, False)
    repo._create_bid(carol_active_p.id, ground_beef.id, 2, False)

    # Bananas - interested only from alice
    repo._create_bid(alice_active_p.id, bananas.id, 0, True)

    # Confirmed run - test user is leader, all are ready
    test_confirmed_p = next(
        (p for p in repo._participations.values() if p.user_id == test_user.id and p.run_id == run_confirmed.id), None
    )
    test_confirmed_p.is_ready = True
    alice_confirmed_p = repo._create_participation(alice.id, run_confirmed.id, is_leader=False, is_ready=True)
    bob_confirmed_p = repo._create_participation(bob.id, run_confirmed.id, is_leader=False, is_ready=True)
    carol_confirmed_p = repo._create_participation(carol.id, run_confirmed.id, is_leader=False, is_ready=True)

    # All users want olive oil
    repo._create_bid(test_confirmed_p.id, olive_oil.id, 1, False)
    repo._create_bid(alice_confirmed_p.id, olive_oil.id, 1, False)
    repo._create_bid(bob_confirmed_p.id, olive_oil.id, 2, False)
    repo._create_bid(carol_confirmed_p.id, olive_oil.id, 1, False)

    # Quinoa - just alice and carol
    repo._create_bid(alice_confirmed_p.id, quinoa.id, 1, False)
    repo._create_bid(carol_confirmed_p.id, quinoa.id, 1, False)

    # Paper Towels - everyone interested
    repo._create_bid(test_confirmed_p.id, paper_towels.id, 1, False)
    repo._create_bid(alice_confirmed_p.id, paper_towels.id, 2, False)
    repo._create_bid(bob_confirmed_p.id, paper_towels.id, 1, False)
    repo._create_bid(carol_confirmed_p.id, paper_towels.id, 0, True)  # interested only

    # Shopping run - test user is leader, has shopping list items
    test_shopping_p = next(
        (p for p in repo._participations.values() if p.user_id == test_user.id and p.run_id == run_shopping.id), None
    )
    test_shopping_p.is_ready = True
    alice_shopping_p = repo._create_participation(alice.id, run_shopping.id, is_leader=False, is_ready=True)
    bob_shopping_p = repo._create_participation(bob.id, run_shopping.id, is_leader=False, is_ready=True)

    # Create bids for shopping run
    repo._create_bid(test_shopping_p.id, detergent.id, 1, False)
    repo._create_bid(alice_shopping_p.id, laundry_pods.id, 1, False)
    repo._create_bid(bob_shopping_p.id, ground_beef.id, 2, False)

    # Shopping list items for shopping run
    shopping_item1 = repo._create_shopping_list_item(run_shopping.id, detergent.id, 1)
    shopping_item1.is_purchased = False
    shopping_item1.purchase_order = 1

    shopping_item2 = repo._create_shopping_list_item(run_shopping.id, laundry_pods.id, 1)
    shopping_item2.is_purchased = False
    shopping_item2.purchase_order = 2

    shopping_item3 = repo._create_shopping_list_item(run_shopping.id, ground_beef.id, 2)
    shopping_item3.is_purchased = False
    shopping_item3.purchase_order = 3

    # Adjusting run - quantities fell short, some users need to adjust bids
    test_adjusting_p = next(
        (p for p in repo._participations.values() if p.user_id == test_user.id and p.run_id == run_adjusting.id), None
    )
    test_adjusting_p.is_ready = True
    alice_adjusting_p = repo._create_participation(alice.id, run_adjusting.id, is_leader=False, is_ready=True)
    bob_adjusting_p = repo._create_participation(bob.id, run_adjusting.id, is_leader=False, is_ready=True)
    carol_adjusting_p = repo._create_participation(carol.id, run_adjusting.id, is_leader=False, is_ready=True)

    # Bids for adjusting run
    # Olive Oil - fully purchased (3 requested, 3 bought)
    repo._create_bid(test_adjusting_p.id, olive_oil.id, 1, False)
    repo._create_bid(alice_adjusting_p.id, olive_oil.id, 2, False)

    # Quinoa - fully purchased (4 requested, 4 bought)
    repo._create_bid(bob_adjusting_p.id, quinoa.id, 2, False)
    repo._create_bid(alice_adjusting_p.id, quinoa.id, 2, False)

    # Paper Towels - SHORTAGE (6 requested, 3 bought)
    repo._create_bid(test_adjusting_p.id, paper_towels.id, 2, False)
    repo._create_bid(alice_adjusting_p.id, paper_towels.id, 2, False)
    repo._create_bid(bob_adjusting_p.id, paper_towels.id, 2, False)

    # Almond Butter - NOT PURCHASED (2 requested, 0 bought)
    bid1 = repo._create_bid(test_adjusting_p.id, almond_butter.id, 1, False)
    bid2 = repo._create_bid(alice_adjusting_p.id, almond_butter.id, 1, False)

    # Frozen Berries - NOT PURCHASED (3 requested, 0 bought)
    bid3 = repo._create_bid(bob_adjusting_p.id, frozen_berries.id, 3, False)

    # Shopping list items for adjusting run
    from decimal import Decimal

    adj_item1 = repo._create_shopping_list_item(run_adjusting.id, olive_oil.id, 3)
    adj_item1.purchased_quantity = 3  # Fully purchased
    adj_item1.purchased_price_per_unit = Decimal('24.99')
    adj_item1.purchased_total = Decimal('74.97')
    adj_item1.is_purchased = True
    adj_item1.purchase_order = 1

    adj_item2 = repo._create_shopping_list_item(run_adjusting.id, quinoa.id, 4)
    adj_item2.purchased_quantity = 4  # Fully purchased
    adj_item2.purchased_price_per_unit = Decimal('18.99')
    adj_item2.purchased_total = Decimal('75.96')
    adj_item2.is_purchased = True
    adj_item2.purchase_order = 2

    adj_item3 = repo._create_shopping_list_item(run_adjusting.id, paper_towels.id, 6)
    adj_item3.purchased_quantity = 3  # SHORTAGE: only 3 out of 6 bought
    adj_item3.purchased_price_per_unit = Decimal('19.99')
    adj_item3.purchased_total = Decimal('59.97')
    adj_item3.is_purchased = True
    adj_item3.purchase_order = 3

    adj_item4 = repo._create_shopping_list_item(run_adjusting.id, almond_butter.id, 2)
    adj_item4.purchased_quantity = 0  # NOT PURCHASED
    adj_item4.purchased_price_per_unit = None
    adj_item4.purchased_total = None
    adj_item4.is_purchased = True
    adj_item4.purchase_order = None

    adj_item5 = repo._create_shopping_list_item(run_adjusting.id, frozen_berries.id, 3)
    adj_item5.purchased_quantity = 0  # NOT PURCHASED
    adj_item5.purchased_price_per_unit = None
    adj_item5.purchased_total = None
    adj_item5.is_purchased = True
    adj_item5.purchase_order = None

    # Distributing run - items purchased, being distributed
    test_distributing_p = next(
        (p for p in repo._participations.values() if p.user_id == test_user.id and p.run_id == run_distributing.id), None
    )
    test_distributing_p.is_ready = True
    alice_distributing_p = repo._create_participation(alice.id, run_distributing.id, is_leader=False, is_ready=True)
    bob_distributing_p = repo._create_participation(bob.id, run_distributing.id, is_leader=False, is_ready=True)

    # Bids with distributed quantities
    bid6 = repo._create_bid(test_distributing_p.id, rotisserie_chicken.id, 2, False)
    bid6.distributed_quantity = 2
    bid6.distributed_price_per_unit = 4.99

    bid7 = repo._create_bid(alice_distributing_p.id, rotisserie_chicken.id, 1, False)
    bid7.distributed_quantity = 1
    bid7.distributed_price_per_unit = 4.99

    bid8 = repo._create_bid(bob_distributing_p.id, toilet_paper.id, 1, False)
    bid8.distributed_quantity = 1
    bid8.distributed_price_per_unit = 22.99

    bid9 = repo._create_bid(test_distributing_p.id, coffee_beans.id, 2, False)
    bid9.distributed_quantity = 2
    bid9.distributed_price_per_unit = 14.99

    # Shopping list items
    shopping_item6 = repo._create_shopping_list_item(run_distributing.id, rotisserie_chicken.id, 3)  # 2 + 1
    shopping_item6.is_purchased = True
    shopping_item6.actual_price = 4.99
    shopping_item6.actual_quantity = 3
    shopping_item6.purchase_order = 1

    shopping_item7 = repo._create_shopping_list_item(run_distributing.id, toilet_paper.id, 1)
    shopping_item7.is_purchased = True
    shopping_item7.actual_price = 22.99
    shopping_item7.actual_quantity = 1
    shopping_item7.purchase_order = 2

    shopping_item8 = repo._create_shopping_list_item(run_distributing.id, coffee_beans.id, 2)
    shopping_item8.is_purchased = True
    shopping_item8.actual_price = 14.99
    shopping_item8.actual_quantity = 2
    shopping_item8.purchase_order = 3

    # Distribution records for distributing run
    alice_distributing_p.picked_up_at = None
    bob_distributing_p.picked_up_at = None

    # Completed run - all done
    test_completed_p = next(
        (p for p in repo._participations.values() if p.user_id == test_user.id and p.run_id == run_completed.id), None
    )
    test_completed_p.is_ready = True
    from datetime import datetime, timedelta, timezone
    test_completed_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=13)

    alice_completed_p = repo._create_participation(alice.id, run_completed.id, is_leader=False, is_ready=True)
    alice_completed_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=13)

    # Bids for completed run
    bid10 = repo._create_bid(test_completed_p.id, detergent.id, 1, False)
    bid10.distributed_quantity = 1
    bid10.distributed_price_per_unit = 16.98

    bid11 = repo._create_bid(alice_completed_p.id, laundry_pods.id, 1, False)
    bid11.distributed_quantity = 1
    bid11.distributed_price_per_unit = 18.98

    # Shopping list items
    shopping_item9 = repo._create_shopping_list_item(run_completed.id, detergent.id, 1)
    shopping_item9.is_purchased = True
    shopping_item9.actual_price = 16.98
    shopping_item9.actual_quantity = 1
    shopping_item9.purchase_order = 1

    shopping_item10 = repo._create_shopping_list_item(run_completed.id, laundry_pods.id, 1)
    shopping_item10.is_purchased = True
    shopping_item10.actual_price = 18.98
    shopping_item10.actual_quantity = 1
    shopping_item10.purchase_order = 2

    # Additional completed runs for price history
    # run_completed_2 (30 days ago)
    test_completed_2_p = next(
        (p for p in repo._participations.values() if p.user_id == test_user.id and p.run_id == run_completed_2.id), None
    )
    test_completed_2_p.is_ready = True
    test_completed_2_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=29)

    bob_completed_2_p = repo._create_participation(bob.id, run_completed_2.id, is_leader=False, is_ready=True)
    bob_completed_2_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=29)

    bid12 = repo._create_bid(test_completed_2_p.id, olive_oil.id, 1, False)
    bid12.distributed_quantity = 1
    bid12.distributed_price_per_unit = 23.99

    bid13 = repo._create_bid(bob_completed_2_p.id, paper_towels.id, 1, False)
    bid13.distributed_quantity = 1
    bid13.distributed_price_per_unit = 19.99

    shopping_item11 = repo._create_shopping_list_item(run_completed_2.id, olive_oil.id, 1)
    shopping_item11.is_purchased = True
    shopping_item11.actual_price = 23.99
    shopping_item11.actual_quantity = 1
    shopping_item11.purchase_order = 1

    shopping_item12 = repo._create_shopping_list_item(run_completed_2.id, paper_towels.id, 1)
    shopping_item12.is_purchased = True
    shopping_item12.actual_price = 19.99
    shopping_item12.actual_quantity = 1
    shopping_item12.purchase_order = 2

    # run_completed_3 (45 days ago) - alice is leader
    alice_completed_3_p = next(
        (p for p in repo._participations.values() if p.user_id == alice.id and p.run_id == run_completed_3.id), None
    )
    alice_completed_3_p.is_ready = True
    alice_completed_3_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=44)

    carol_completed_3_p = repo._create_participation(carol.id, run_completed_3.id, is_leader=False, is_ready=True)
    carol_completed_3_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=44)

    bid14 = repo._create_bid(alice_completed_3_p.id, detergent.id, 2, False)
    bid14.distributed_quantity = 2
    bid14.distributed_price_per_unit = 15.98

    shopping_item13 = repo._create_shopping_list_item(run_completed_3.id, detergent.id, 2)
    shopping_item13.is_purchased = True
    shopping_item13.actual_price = 15.98
    shopping_item13.actual_quantity = 2
    shopping_item13.purchase_order = 1

    # run_completed_4 (60 days ago) - bob is leader
    bob_completed_4_p = next(
        (p for p in repo._participations.values() if p.user_id == bob.id and p.run_id == run_completed_4.id), None
    )
    bob_completed_4_p.is_ready = True
    bob_completed_4_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=59)

    shopping_item14 = repo._create_shopping_list_item(run_completed_4.id, olive_oil.id, 1)
    shopping_item14.is_purchased = True
    shopping_item14.actual_price = 24.99
    shopping_item14.actual_quantity = 1
    shopping_item14.purchase_order = 1

    bid15 = repo._create_bid(bob_completed_4_p.id, olive_oil.id, 1, False)
    bid15.distributed_quantity = 1
    bid15.distributed_price_per_unit = 24.99

    # run_completed_5 (75 days ago) - bob is leader, work group
    bob_completed_5_p = next(
        (p for p in repo._participations.values() if p.user_id == bob.id and p.run_id == run_completed_5.id), None
    )
    bob_completed_5_p.is_ready = True
    bob_completed_5_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=74)

    carol_completed_5_p = repo._create_participation(carol.id, run_completed_5.id, is_leader=False, is_ready=True)
    carol_completed_5_p.picked_up_at = datetime.now(timezone.utc) - timedelta(days=74)

    bid16 = repo._create_bid(bob_completed_5_p.id, ground_beef.id, 1, False)
    bid16.distributed_quantity = 1
    bid16.distributed_price_per_unit = 16.48

    shopping_item15 = repo._create_shopping_list_item(run_completed_5.id, ground_beef.id, 1)
    shopping_item15.is_purchased = True
    shopping_item15.actual_price = 16.48
    shopping_item15.actual_quantity = 1
    shopping_item15.purchase_order = 1
