
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from datetime import datetime


from pydantic import EmailStr


# User registration
class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8)

class Token(BaseModel):
    access_token: str
    token_type: str

# User login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# User response
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Schema for creating a product
class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    sku: str = Field(min_length=2, max_length=50)
    description: str | None = None
    price: Decimal = Field(gt=0)
    stock_quantity: int = Field(default=0, ge=0)


# Schema for updating a product
class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    sku: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)


# Schema for displaying a product
class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    description: str | None
    price: Decimal
    stock_quantity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)

class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: Decimal
    status: str
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)

class OrderStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(pending|confirmed|shipped|delivered|cancelled)$"
    )

class OrderStatusUpdate(BaseModel):
    status: str = Field(
        pattern="^(pending|confirmed|shipped|delivered)$"
    )