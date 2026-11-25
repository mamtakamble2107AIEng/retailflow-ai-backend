
from app.security import hash_password, verify_password

password = "SecurePass123"

# Generate password hash
hashed = hash_password(password)

print("Original password:", password)
print("Generated hash:", hashed)

# Verify correct password
print("Correct password:", verify_password(password, hashed))

# Verify incorrect password
print("Wrong password:", verify_password("WrongPass123", hashed))
