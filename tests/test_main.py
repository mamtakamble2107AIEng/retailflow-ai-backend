
from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.auth import get_current_user
from app.database import Base
from app.dependencies import get_db
from app.models import Product
from app.models import User
from app.security import verify_password

# Create a separate temporary SQLite database for testing.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)

# Create the test database tables.
Base.metadata.create_all(bind=test_engine)


# Provide a separate database session to API tests.
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Simulate customer and admin accounts.
test_customer = SimpleNamespace(
    id=1,
    full_name="Test Customer",
    email="test@example.com",
    role="customer",
    is_active=True
)

test_admin = SimpleNamespace(
    id=2,
    full_name="Test Admin",
    email="admin@example.com",
    role="admin",
    is_active=True
)


# Replace the application's database dependency.
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = lambda: test_customer

client = TestClient(app)


# Insert one sample product into the test database.
with TestingSessionLocal() as db:
    db.add(
        Product(
            name="Test Product",
            sku="TEST-PROD-001",
            description="Sample product",
            price=100,
            stock_quantity=5
        )
    )
    db.commit()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200


def test_get_all_products():
    response = client.get("/products")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_single_product():
    response = client.get("/products")
    products = response.json()

    assert len(products) > 0

    product_id = products[0]["id"]
    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["id"] == product_id


def test_get_nonexistent_product():
    response = client.get("/products/999999")
    assert response.status_code == 404


def test_create_product_without_admin():
    response = client.post(
        "/products",
        json={
            "name": "Test Keyboard",
            "sku": "TEST-KEY-001",
            "price": 1500,
            "stock_quantity": 10
        }
    )

    assert response.status_code == 403


def test_create_product_as_admin():
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        response = client.post(
            "/products",
            json={
                "name": "Test Keyboard",
                "sku": "TEST-KEY-002",
                "description": "Automated test product",
                "price": 1500,
                "stock_quantity": 10
            }
        )

        assert response.status_code == 201
        assert response.json()["sku"] == "TEST-KEY-002"

    finally:
        app.dependency_overrides[get_current_user] = lambda: test_customer

def test_create_product_duplicate_sku():
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        response = client.post(
            "/products",
            json={
                "name": "Duplicate Product",
                "sku": "TEST-PROD-001",
                "description": "Testing duplicate SKU",
                "price": 2000,
                "stock_quantity": 5
            }
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Product SKU already exists"

    finally:
        app.dependency_overrides[get_current_user] = lambda: test_customer

def test_create_product_with_negative_price():
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        response = client.post(
            "/products",
            json={
                "name": "Invalid Price Product",
                "sku": "TEST-INVALID-PRICE",
                "price": -100,
                "stock_quantity": 5
            }
        )

        assert response.status_code == 422

    finally:
        app.dependency_overrides[get_current_user] = lambda: test_customer


def test_create_product_with_negative_stock():
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        response = client.post(
            "/products",
            json={
                "name": "Invalid Stock Product",
                "sku": "TEST-INVALID-STOCK",
                "price": 100,
                "stock_quantity": -5
            }
        )

        assert response.status_code == 422

    finally:
        app.dependency_overrides[get_current_user] = lambda: test_customer


def test_update_product_as_admin():
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        # Find the sample product in the test database.
        response = client.get("/products")
        product_id = response.json()[0]["id"]

        # Update the product.
        response = client.put(
            f"/products/{product_id}",
            json={
                "name": "Updated Test Product",
                "sku": "TEST-PROD-UPDATED",
                "description": "Updated using automated testing",
                "price": 2500,
                "stock_quantity": 20
            }
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Test Product"
        assert response.json()["sku"] == "TEST-PROD-UPDATED"

    finally:
        app.dependency_overrides[get_current_user] = lambda: test_customer



def test_update_product_with_duplicate_sku():
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        response = client.post("/products")

        # Get the existing sample products.
        products = client.get("/products").json()

        # Use the first and second product IDs.
        first_product_id = products[0]["id"]
        second_product_sku = products[1]["sku"]

        response = client.put(
            f"/products/{first_product_id}",
            json={
                "name": "Duplicate SKU Test",
                "sku": second_product_sku,
                "description": "Testing duplicate SKU",
                "price": 2000,
                "stock_quantity": 10
            }
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "SKU already belongs to another product"

    finally:
        app.dependency_overrides[get_current_user] = lambda: test_customer


def test_patch_product_as_admin():
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        products = client.get("/products").json()
        product_id = products[0]["id"]

        original_name = products[0]["name"]
        original_sku = products[0]["sku"]

        response = client.patch(
            f"/products/{product_id}",
            json={"price": 3000}
        )

        assert response.status_code == 200
        assert float(response.json()["price"]) == 3000.0
        assert response.json()["name"] == original_name
        assert response.json()["sku"] == original_sku

    finally:
        app.dependency_overrides[get_current_user] = lambda: test_customer


def test_delete_product_as_admin():
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        # Create a product specifically for deletion.
        create_response = client.post(
            "/products",
            json={
                "name": "Product To Delete",
                "sku": "TEST-DELETE-001",
                "description": "Temporary deletion test",
                "price": 500,
                "stock_quantity": 5
            }
        )

        assert create_response.status_code == 201

        product_id = create_response.json()["id"]

        # Delete the product.
        delete_response = client.delete(
            f"/products/{product_id}"
        )

        assert delete_response.status_code == 200

        # Verify the product no longer exists.
        get_response = client.get(
            f"/products/{product_id}"
        )

        assert get_response.status_code == 404

    finally:
        app.dependency_overrides[get_current_user] = lambda: test_customer



def test_register_user_successfully():
    response = client.post(
        "/auth/register",
        json={
            "full_name": "New Test User",
            "email": "newuser@example.com",
            "password": "TestPass123"
        }
    )

    assert response.status_code == 201
    assert response.json()["email"] == "newuser@example.com"
    assert "password" not in response.json()
    assert "hashed_password" not in response.json()


def test_register_user_duplicate_email():
    user_data = {
        "full_name": "Duplicate User",
        "email": "duplicate@example.com",
        "password": "TestPass123"
    }

    first_response = client.post("/auth/register", json=user_data)
    second_response = client.post("/auth/register", json=user_data)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_registered_password_is_hashed():
    email = "hashcheck@example.com"

    response = client.post(
        "/auth/register",
        json={
            "full_name": "Hash Check",
            "email": email,
            "password": "TestPass123"
        }
    )

    assert response.status_code == 201

    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()

        assert user is not None
        assert user.hashed_password != "TestPass123"
        assert verify_password("TestPass123", user.hashed_password)


def test_login_successfully():
    client.post(
        "/auth/register",
        json={
            "full_name": "Login Test User",
            "email": "login@example.com",
            "password": "TestPass123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "TestPass123"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_with_wrong_password():
    client.post(
        "/auth/register",
        json={
            "full_name": "Wrong Password User",
            "email": "wrongpass@example.com",
            "password": "TestPass123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPass123"
        }
    )

    assert response.status_code == 401


def test_login_with_unknown_email():
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "TestPass123"
        }
    )

    assert response.status_code == 401


def test_login_with_inactive_account():
    client.post(
        "/auth/register",
        json={
            "full_name": "Inactive User",
            "email": "inactive@example.com",
            "password": "TestPass123"
        }
    )

    with TestingSessionLocal() as db:
        user = db.query(User).filter(
            User.email == "inactive@example.com"
        ).first()

        user.is_active = False
        db.commit()

    response = client.post(
        "/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "TestPass123"
        }
    )

    assert response.status_code == 403



def create_test_product(sku, stock=10, price=100):
    with TestingSessionLocal() as db:
        product = Product(
            name="Order Test Product",
            sku=sku,
            description="Product for order testing",
            price=price,
            stock_quantity=stock
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product.id


def test_create_order_successfully():
    product_id = create_test_product("ORDER-TEST-001", stock=10, price=100)

    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2
                }
            ]
        }
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert float(response.json()["total_amount"]) == 200.0
    assert len(response.json()["items"]) == 1

    with TestingSessionLocal() as db:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        assert product.stock_quantity == 8



def test_create_order_with_insufficient_stock():
    product_id = create_test_product(
        "ORDER-TEST-002",
        stock=2,
        price=100
    )

    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 5
                }
            ]
        }
    )

    assert response.status_code == 400

    with TestingSessionLocal() as db:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        assert product.stock_quantity == 2


def test_create_order_with_invalid_product():
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": 999999,
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 404


def test_duplicate_product_items_cannot_oversell_stock():
    product_id = create_test_product(
        "ORDER-TEST-DUPLICATE",
        stock=5,
        price=100
    )

    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 4
                },
                {
                    "product_id": product_id,
                    "quantity": 4
                }
            ]
        }
    )

    assert response.status_code == 400

    with TestingSessionLocal() as db:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        assert product.stock_quantity == 5


def test_cancel_order_restores_inventory():
    # Create product with 10 units
    product_id = create_test_product(
        "ORDER-CANCEL-001",
        stock=10,
        price=100
    )

    # Customer places an order for 3 units
    order_response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 3
                }
            ]
        }
    )

    assert order_response.status_code == 201

    order_id = order_response.json()["id"]

    # Verify stock decreased to 7
    with TestingSessionLocal() as db:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        assert product.stock_quantity == 7

    # Switch authenticated user to admin
    previous_override = app.dependency_overrides.get(
        get_current_user
    )

    app.dependency_overrides[get_current_user] = (
        lambda: test_admin
    )

    try:
        cancel_response = client.post(
            f"/admin/orders/{order_id}/cancel"
        )

        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "cancelled"

    finally:
        if previous_override is not None:
            app.dependency_overrides[get_current_user] = previous_override
        else:
            app.dependency_overrides.pop(get_current_user, None)

    # Verify inventory restored to 10
    with TestingSessionLocal() as db:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        assert product.stock_quantity == 10



def test_cannot_cancel_order_twice():
    product_id = create_test_product(
        "ORDER-CANCEL-002",
        stock=10,
        price=100
    )

    order_response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2
                }
            ]
        }
    )

    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    previous_override = app.dependency_overrides.get(
        get_current_user
    )
    app.dependency_overrides[get_current_user] = lambda: test_admin

    try:
        first_response = client.post(
            f"/admin/orders/{order_id}/cancel"
        )

        second_response = client.post(
            f"/admin/orders/{order_id}/cancel"
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 409

    finally:
        if previous_override is not None:
            app.dependency_overrides[get_current_user] = previous_override
        else:
            app.dependency_overrides.pop(get_current_user, None)

    with TestingSessionLocal() as db:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        assert product.stock_quantity == 10



def test_global_exception_handler():
    @app.get("/test-server-error")
    def trigger_server_error():
        raise RuntimeError("Internal test error")

    test_client = TestClient(
        app,
        raise_server_exceptions=False
    )

    response = test_client.get("/test-server-error")

    assert response.status_code == 500
    assert response.json()["success"] is False
    assert response.json()["message"] == "Internal server error"
    assert response.json()["path"] == "/test-server-error"
