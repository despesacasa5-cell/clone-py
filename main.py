from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
from mongo_session import load_session, save_session
from scheduler import setup_scheduler
from dialogs import listar_e_salvar_dialogs
from api import app
from contextlib import asynccontextmanager
import uvicorn
import os
import state
from keepalive import keepalive
import asyncio

load_dotenv()

api_id       = os.getenv('API_ID')
api_hash     = os.getenv('API_HASH')
mongo_uri    = os.getenv('MONGO_URI')
session_name = 'minha_session'

session_string = load_session(mongo_uri, session_name)
session = StringSession(session_string) if session_string else StringSession()
client = TelegramClient(session, api_id, api_hash)


@asynccontextmanager
async def lifespan(app):
    await client.connect()
    await client.start()

    state.telegram_client = client
    save_session(mongo_uri, session_name, client.session.save())
    print("✅ Conectado ao Telegram!\n")

    await listar_e_salvar_dialogs(client, mongo_uri)

    # Inicia keepalive em background
    task = asyncio.create_task(keepalive())
    print("💓 Keepalive iniciado!\n")

    yield

    # Cancela o keepalive ao encerrar
    task.cancel()
    await client.disconnect()
    print("🔴 Desconectado.")