

from sqlalchemy.sql import func
from sqlalchemy import Boolean
from app.database import Base
from sqlalchemy import (
    Column, Integer, String, Text, Numeric,
    TIMESTAMP, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="customer", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String(150), nullable=False)

    sku = Column(String(50), unique=True, nullable=False)

    description = Column(Text, nullable=True)

    price = Column(Numeric(10, 2), nullable=False)

    stock_quantity = Column(Integer, default=0)

    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp()
    )

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(30), default="pending", nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
