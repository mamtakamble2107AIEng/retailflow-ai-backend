
from app.schemas import UserCreate

user = UserCreate(
    full_name="Amol Kamble",
    email="amol@example.com",
    password="SecurePass123"
)

print(user)
print("User schema validation successful!")
