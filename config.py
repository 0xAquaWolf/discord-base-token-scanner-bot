import os
from dotenv import load_dotenv


def load_config():
    load_dotenv()
    return {
        "DISCORD_BOT_TOKEN": os.getenv("BASE_TOKEN_SNIFFER"),
        "STAGING_CHANNEL_ID": int(os.getenv("STAGING_CHANNEL_ID")),
        "BASESCAN_API_TOKEN": os.getenv("BASESCAN_API_TOKEN"),
        "DEBUG_MODE": os.getenv("DEBUG_MODE", "False").lower() == "true",
        "DB_NAME": os.getenv("DB_NAME"),
        "DB_USER": os.getenv("DB_USER"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        "DB_HOST": os.getenv("DB_HOST"),
        "DB_PORT": os.getenv("DB_PORT"),
    }
