
from app.schemas import ProductCreate

product = ProductCreate(
    name="Dell Laptop",
    sku="LAP004",
    description="Dell business laptop",
    price=65000.00,
    stock_quantity=12
)

print(product)
print("Schema validation successful!")
