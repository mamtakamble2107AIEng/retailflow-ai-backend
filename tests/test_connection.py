
from sqlalchemy import text
from app.database import engine

try:
    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT VERSION(), DATABASE()")
        )

        version, database = result.fetchone()

        print("Successfully connected to MySQL!")
        print("MySQL Version:", version)
        print("Database Name:", database)

except Exception as error:
    print("Database connection failed!")
    print("Error:", error)
