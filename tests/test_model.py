
from app.models import Product

print("Product model loaded successfully!")
print("Table name:", Product.__tablename__)

for column in Product.__table__.columns:
    print(column.name, column.type)
