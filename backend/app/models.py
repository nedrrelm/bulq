from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, DateTime, ForeignKey, Table, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from .run_state import RunState

Base = declarative_base()

group_membership = Table(
    'group_membership',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('group_id', UUID(as_uuid=True), ForeignKey('groups.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    groups = relationship("Group", secondary=group_membership, back_populates="members")
    created_groups = relationship("Group", back_populates="creator")
    run_participations = relationship("RunParticipation", back_populates="user")

class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    invite_token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()), index=True)

    creator = relationship("User", back_populates="created_groups")
    members = relationship("User", secondary=group_membership, back_populates="groups")
    runs = relationship("Run", back_populates="group")

class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

    runs = relationship("Run", back_populates="store")
    products = relationship("Product", back_populates="store")

class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=False, index=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False, index=True)
    state = Column(String, nullable=False, default=RunState.PLANNING, index=True)

    # State transition timestamps
    planning_at = Column(DateTime(timezone=True), server_default=func.now())
    active_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    shopping_at = Column(DateTime(timezone=True), nullable=True)
    adjusting_at = Column(DateTime(timezone=True), nullable=True)
    distributing_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    group = relationship("Group", back_populates="runs")
    store = relationship("Store", back_populates="runs")
    participations = relationship("RunParticipation", back_populates="run")

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False, index=True)
    name = Column(String, nullable=False)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="products")
    product_bids = relationship("ProductBid", back_populates="product")

class RunParticipation(Base):
    __tablename__ = "run_participations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey('runs.id'), nullable=False, index=True)
    is_leader = Column(Boolean, nullable=False, default=False)
    is_ready = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="run_participations")
    run = relationship("Run", back_populates="participations")
    product_bids = relationship("ProductBid", back_populates="participation")

class ProductBid(Base):
    __tablename__ = "product_bids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    participation_id = Column(UUID(as_uuid=True), ForeignKey('run_participations.id'), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)
    interested_only = Column(Boolean, nullable=False, default=False)

    # Distribution fields
    distributed_quantity = Column(Integer, nullable=True)  # Actual quantity allocated to user
    distributed_price_per_unit = Column(DECIMAL(10, 2), nullable=True)  # Price we paid per unit
    is_picked_up = Column(Boolean, nullable=False, default=False)  # Whether user collected their items

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    participation = relationship("RunParticipation", back_populates="product_bids")
    product = relationship("Product", back_populates="product_bids")

class ShoppingListItem(Base):
    __tablename__ = "shopping_list_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey('runs.id'), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False, index=True)
    requested_quantity = Column(Integer, nullable=False)
    encountered_prices = Column(JSON, nullable=False, default=list)  # [{"price": 24.99, "notes": "aisle 3"}, ...]
    purchased_quantity = Column(Integer, nullable=True)
    purchased_price_per_unit = Column(DECIMAL(10, 2), nullable=True)
    purchased_total = Column(DECIMAL(10, 2), nullable=True)
    is_purchased = Column(Boolean, nullable=False, default=False)
    purchase_order = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    run = relationship("Run")
    product = relationship("Product")

