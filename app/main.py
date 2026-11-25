
from fastapi import FastAPI, FastAPI, HTTPException, Request, Depends
from sqlalchemy.orm import Session, selectinload

from app.database import engine
from app.dependencies import get_db
from app.models import Order, OrderItem, Product, User
from app.schemas import ProductCreate, ProductResponse, ProductUpdate, UserCreate, UserResponse, UserLogin, Token, OrderCreate, OrderResponse, OrderStatusUpdate, OrderStatusUpdate
from app.security import hash_password, verify_password
from fastapi.responses import JSONResponse
from app.auth import create_access_token, get_current_user, get_current_admin

from decimal import Decimal
from sqlalchemy import select

# Create FastAPI application
app = FastAPI(
    title="RetailFlow AI Backend",
    description="E-commerce management API",
    version="1.0.0"
)


import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    logger.exception(
        "Unexpected error on %s %s",
        request.method,
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "path": request.url.path
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "path": request.url.path
        }
    )



@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=201
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Check whether email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = hash_password(user_data.password)

    # Create customer account
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password,
        role="customer",
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/auth/login", response_model=Token)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    # Find user by email
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    # Check user and password
    if not user or not verify_password(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Check account status
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    # Generate JWT token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/auth/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return current_user


# Home API
@app.get("/")
def home():
    return {
        "message": "Welcome to RetailFlow AI Backend!",
        "status": "Running successfully"
    }

# Health check API
@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

@app.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Check whether SKU already exists
    existing_product = db.query(Product).filter(
        Product.sku == product.sku
    ).first()

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product SKU already exists"
        )

    # Create a new product
    new_product = Product(**product.model_dump())

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


@app.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    products = db.query(Product).all()
    return products


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product



@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check whether another product uses this SKU
    duplicate_sku = db.query(Product).filter(
        Product.sku == product_data.sku,
        Product.id != product_id
    ).first()

    if duplicate_sku:
        raise HTTPException(
            status_code=400,
            detail="SKU already belongs to another product"
        )

    for key, value in product_data.model_dump().items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


@app.patch("/products/{product_id}", response_model=ProductResponse)
def partial_update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    update_data = product_data.model_dump(exclude_unset=True)

    if "sku" in update_data:
        duplicate_sku = db.query(Product).filter(
            Product.sku == update_data["sku"],
            Product.id != product_id
        ).first()

        if duplicate_sku:
            raise HTTPException(
                status_code=400,
                detail="SKU already belongs to another product"
            )

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully",
        "product_id": product_id
    }


@app.post(
    "/orders",
    response_model=OrderResponse,
    status_code=201
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Step 1: Combine quantities for duplicate product IDs
        requested_quantities = {}

        for item in order_data.items:
            requested_quantities[item.product_id] = (
                requested_quantities.get(item.product_id, 0)
                + item.quantity
            )

        # Step 2: Initialize order details
        total_amount = Decimal("0.00")
        order_items = []

        # Step 3: Lock and validate products
        for product_id in sorted(requested_quantities):
            quantity = requested_quantities[product_id]

            product = db.execute(
                select(Product)
                .where(Product.id == product_id)
                .with_for_update()
            ).scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {product_id} not found"
                )

            if product.stock_quantity < quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {product.name}"
                )

            # Step 4: Calculate order total
            item_price = Decimal(str(product.price))
            total_amount += item_price * quantity

            order_items.append({
                "product": product,
                "quantity": quantity,
                "unit_price": item_price
            })

        # Step 5: Create main order
        new_order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            status="pending"
        )

        db.add(new_order)
        db.flush()

        # Step 6: Add order items and reduce inventory
        for item in order_items:
            product = item["product"]

            product.stock_quantity -= item["quantity"]

            new_order.items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item["quantity"],
                    unit_price=item["unit_price"]
                )
            )

        # Step 7: Commit transaction
        db.commit()

        # Step 8: Reload order with its items
        saved_order = db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == new_order.id)
        ).scalar_one()

        return saved_order

    except Exception:
        db.rollback()
        raise

@app.get("/orders/my-orders", response_model=list[OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    ).scalars().all()

    return orders

@app.get("/admin/orders", response_model=list[OrderResponse])
def get_all_orders(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    orders = db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    ).scalars().all()

    return orders

@app.patch("/admin/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    order.status = status_data.status

    db.commit()
    db.refresh(order)

    return {
        "message": "Order status updated successfully",
        "order_id": order.id,
        "status": order.status
    }

@app.post("/admin/orders/{order_id}/cancel")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    try:
        # Lock the order to prevent simultaneous cancellation
        order = db.execute(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        ).scalar_one_or_none()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if order.status == "cancelled":
            raise HTTPException(
                status_code=409,
                detail="Order is already cancelled"
            )

        if order.status not in ["pending", "confirmed"]:
            raise HTTPException(
                status_code=400,
                detail="Only pending or confirmed orders can be cancelled"
            )

        # Restore each product's inventory
        for item in order.items:
            product = db.execute(
                select(Product)
                .where(Product.id == item.product_id)
                .with_for_update()
            ).scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found"
                )

            product.stock_quantity += item.quantity

        order.status = "cancelled"

        db.commit()

        return {
            "message": "Order cancelled and inventory restored",
            "order_id": order.id,
            "status": order.status
        }

    except Exception:
        db.rollback()
        raise

