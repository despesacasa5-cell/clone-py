from telethon import TelegramClient
from dotenv import load_dotenv
from mongo_session import MongoSession
import os

load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
mongo_uri = os.getenv('MONGO_URI')

session = MongoSession(mongo_uri, 'minha_session')
client = TelegramClient(session, api_id, api_hash)

async def main():
    await client.start()
    print("Conectado e session salva no MongoDB!")

with client:
    client.loop.run_until_complete(main())