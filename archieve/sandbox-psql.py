import psycopg2
from psycopg2 import sql
import random
import string

# from datetime import datetime
from dotenv import load_dotenv
# import os

load_dotenv()
# DB_HOST = os.getenv("DB_HOST")
# DB_NAME = os.getenv("DB_NAME")
# DB_USER = os.getenv("DB_USER")
# DB_PASS = os.getenv("DB_PASS")

DB_HOST = "localhost"
DB_NAME = ""
DB_USER = "postgres"
DB_PASS = ""
DB_PORT = "5432"

# Database connection parameters
db_params = {
    "host": DB_HOST,
    "database": DB_NAME,
    "user": DB_USER,
    "password": DB_PASS,
}


def connect_to_db():
    """Establish a connection to the database."""
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except (Exception, psycopg2.Error) as error:
        print("Error connecting to PostgreSQL database:", error)
        return None


def create_token_pair(conn, token_data):
    """Insert a new token pair into the database."""
    try:
        cursor = conn.cursor()
        insert_query = sql.SQL("""
            INSERT INTO new_token_pairs (
                token_name, symbol, decimals, total_supply, deployer_address,
                deployer_tx_hash, basescan_token_link, dexscreener_token_link,
                basescan_deployer_link
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id;
        """)
        cursor.execute(insert_query, token_data)
        new_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Token pair created with ID: {new_id}")
        return new_id
    except (Exception, psycopg2.Error) as error:
        print("Error creating token pair:", error)
        conn.rollback()
        return None


def get_token_pair(conn, token_id):
    """Retrieve a token pair by ID."""
    try:
        cursor = conn.cursor()
        select_query = "SELECT * FROM new_token_pairs WHERE id = %s;"
        cursor.execute(select_query, (token_id,))
        token = cursor.fetchone()
        if token:
            print("Token pair found:", token)
        else:
            print("Token pair not found.")
        return token
    except (Exception, psycopg2.Error) as error:
        print("Error retrieving token pair:", error)
        return None


def update_token_pair(conn, token_id, update_data):
    """Update an existing token pair."""
    try:
        cursor = conn.cursor()
        update_query = sql.SQL("""
            UPDATE new_token_pairs
            SET {} = %s
            WHERE id = %s;
        """).format(sql.Identifier(update_data[0]))
        cursor.execute(update_query, (update_data[1], token_id))
        conn.commit()
        print(f"Token pair with ID {token_id} updated.")
    except (Exception, psycopg2.Error) as error:
        print("Error updating token pair:", error)
        conn.rollback()


def delete_token_pair(conn, token_id):
    """Delete a token pair by ID."""
    try:
        cursor = conn.cursor()
        delete_query = "DELETE FROM new_token_pairs WHERE id = %s;"
        cursor.execute(delete_query, (token_id,))
        conn.commit()
        print(f"Token pair with ID {token_id} deleted.")
    except (Exception, psycopg2.Error) as error:
        print("Error deleting token pair:", error)
        conn.rollback()


def generate_random_address():
    """Generate a random Ethereum-like address."""
    return "0x" + "".join(random.choices(string.hexdigits, k=40))


def generate_random_hash():
    """Generate a random transaction hash."""
    return "0x" + "".join(random.choices(string.hexdigits, k=64))


def generate_sample_token_data():
    """Generate sample data for a token pair."""
    token_name = f"Token{random.randint(1000, 9999)}"
    symbol = "".join(random.choices(string.ascii_uppercase, k=3))
    decimals = random.choice([6, 8, 18])
    total_supply = random.randint(1000000, 1000000000) * (10**decimals)
    deployer_address = generate_random_address()
    deployer_tx_hash = generate_random_hash()
    basescan_token_link = f"https://basescan.org/token/{generate_random_address()}"
    dexscreener_token_link = f"https://dexscreener.com/base/{generate_random_address()}"
    basescan_deployer_link = f"https://basescan.org/address/{deployer_address}"

    return (
        token_name,
        symbol,
        decimals,
        total_supply,
        deployer_address,
        deployer_tx_hash,
        basescan_token_link,
        dexscreener_token_link,
        basescan_deployer_link,
    )


def seed_database(conn, num_tokens=10):
    """Seed the database with a specified number of random token pairs."""
    created_ids = []
    for _ in range(num_tokens):
        token_data = generate_sample_token_data()
        new_id = create_token_pair(conn, token_data)
        if new_id:
            created_ids.append(new_id)

    print(f"Created {len(created_ids)} sample token pairs.")
    return created_ids


def clear_database(conn):
    """Clear all data from the new_token_pairs table."""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM new_token_pairs;")
        conn.commit()
        print("All token pairs have been deleted from the database.")
    except (Exception, psycopg2.Error) as error:
        print("Error clearing the database:", error)
        conn.rollback()


def display_all_tokens(conn):
    """Retrieve and display all token pairs in the database."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM new_token_pairs;")
        tokens = cursor.fetchall()

        if tokens:
            print(f"Found {len(tokens)} token pairs:")
            for token in tokens:
                print(token)
        else:
            print("No token pairs found in the database.")

        return tokens
    except (Exception, psycopg2.Error) as error:
        print("Error retrieving token pairs:", error)
        return None


def main():
    conn = connect_to_db()
    if conn is None:
        return

    try:
        # Clear the database
        clear_database(conn)

        # Seed the database with 5 random token pairs
        created_ids = seed_database(conn, 5)

        # Display all tokens
        display_all_tokens(conn)

        # Example of updating a random token
        if created_ids:
            random_id = random.choice(created_ids)
            update_token_pair(conn, random_id, ("symbol", "UPD"))
            print(f"\nAfter updating token with ID {random_id}:")
            get_token_pair(conn, random_id)

        # Example of deleting a random token
        if created_ids:
            random_id = random.choice(created_ids)
            delete_token_pair(conn, random_id)
            print(f"\nAfter deleting token with ID {random_id}:")
            display_all_tokens(conn)

    finally:
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
