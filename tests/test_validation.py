
from app.schemas import ProductCreate
from pydantic import ValidationError

try:
    product = ProductCreate(
        name="Test Laptop",
        sku="TEST001",
        price=-100,
        stock_quantity=-5
    )
    print(product)

except ValidationError as error:
    print("Validation working successfully!")
    print(error)
