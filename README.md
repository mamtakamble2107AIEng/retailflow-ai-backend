# RetailFlow AI Backend

A RESTful e-commerce backend API built with Python and FastAPI. It provides product management, user authentication, role-based access control, order processing, and inventory management.

## Features

- **Product Management:** Create, read, update, and delete products.
- **User Authentication:** User registration, login, and JWT-based authentication.
- **Role-Based Access Control:** Separate permissions for administrators and customers.
- **Order Management:** Create orders and view customer order history.
- **Inventory Management:** Automatic stock deduction when orders are placed.
- **Order Cancellation:** Restore inventory when eligible orders are cancelled.
- **Admin Controls:** View all orders and update order statuses.
- **API Documentation:** Interactive Swagger documentation.

## Technology Stack

- Python
- FastAPI
- MySQL
- SQLAlchemy
- PyMySQL
- Pydantic
- JWT
- Argon2 password hashing
- Uvicorn

## Project Structure

```text
retailflow-backend/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── dependencies.py
│   ├── security.py
│   └── auth.py
├── tests/
├── venv/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure your MySQL database and environment variables in `.env`.
5. Start the application:

```bash
python -m uvicorn app.main:app --reload
```

#python -m pytest tests/test_main.py -v

## API Documentation

After starting the application, open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

## Security Notes

- Store database credentials and JWT secrets in environment variables.
- Never commit `.env` or authentication tokens to GitHub.
- Public user registration creates customer accounts; administrative access is restricted.

## Project Status

Core product management, authentication, authorization, order processing, and inventory workflows have been implemented.

**Author:** Amol Kamble
