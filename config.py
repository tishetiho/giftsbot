import os

BOT_TOKEN = "8628542460:AAG9x0N14OQlqSnhHswzaRSqkd7lo5TdYHY"
BOT_USERNAME = "MellGifts_robot"
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMIN_IDS", "5078764886").split(",")]
DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
