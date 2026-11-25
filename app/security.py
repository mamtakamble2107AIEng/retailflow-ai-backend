
from pwdlib import PasswordHash

# Initialize secure password hashing
password_hash = PasswordHash.recommended()


# Convert plain password into a secure hash
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# Verify entered password against stored hash
def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return password_hash.verify(
        plain_password,
        hashed_password
    )
