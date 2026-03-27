import os

BOT_TOKEN = "7938896805:AAGx7neVzOUXbzl8wSIsSZ93dB4ZxAWhldo"
BOT_USERNAME = "prosnylsa_bot"
ADMIN_IDS = [int(id) for d in os.getenv("ADMIN_IDS", "5078764886").split(",")]
DATABASE_PATH = os.getenv("DATABASE_PATH", "database.db")
