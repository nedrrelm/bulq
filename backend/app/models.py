from sqlalchemy import Column, String, Integer, Boolean, DECIMAL, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

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
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    groups = relationship("Group", secondary=group_membership, back_populates="members")
    created_groups = relationship("Group", back_populates="creator")
    product_bids = relationship("ProductBid", back_populates="user")

class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    invite_token = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

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
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    state = Column(String, nullable=False, default="planning")

    group = relationship("Group", back_populates="runs")
    store = relationship("Store", back_populates="runs")
    product_bids = relationship("ProductBid", back_populates="run")

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_id = Column(UUID(as_uuid=True), ForeignKey('stores.id'), nullable=False)
    name = Column(String, nullable=False)
    base_price = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    store = relationship("Store", back_populates="products")
    product_bids = relationship("ProductBid", back_populates="product")

class ProductBid(Base):
    __tablename__ = "product_bids"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    run_id = Column(UUID(as_uuid=True), ForeignKey('runs.id'), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    interested_only = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="product_bids")
    run = relationship("Run", back_populates="product_bids")
    product = relationship("Product", back_populates="product_bids")