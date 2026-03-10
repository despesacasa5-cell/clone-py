from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
from mongo_session import load_session, save_session, save_pair
from scheduler import setup_scheduler
import asyncio
from dialogs import listar_e_salvar_dialogs
import uvicorn
import threading
from api import app

load_dotenv()

import os
api_id   = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
mongo_uri = os.getenv('MONGO_URI')
session_name = 'minha_session'

session_string = load_session(mongo_uri, session_name)
session = StringSession(session_string) if session_string else StringSession()
client = TelegramClient(session, api_id, api_hash)

async def main():
    await client.start()
    save_session(mongo_uri, session_name, client.session.save())
    print("✅ Conectado ao Telegram!\n")

    # Atualiza lista de diálogos no MongoDB
    await listar_e_salvar_dialogs(client, mongo_uri)

    # ─── Cadastra pares (só precisa rodar uma vez) ───
    # Depois que cadastrar, pode comentar esse bloco
    save_pair(
        mongo_uri,
        name='par_01',
        origem_id=-1001234567890,   # ID do grupo origem
        destino_id=-1009876543210,  # ID do grupo destino
        horarios=['08:00', '12:00', '18:00']
    )
    # ─────────────────────────────────────────────────

    # Inicia o scheduler
    scheduler = setup_scheduler(client, mongo_uri)
    scheduler.start()
    print("\n🚀 Scheduler rodando! Aguardando horários...\n")

    # Mantém o processo vivo no Railway

        # Roda o FastAPI em thread separada
    threading.Thread(
        target=uvicorn.run,
        args=(app,),
        kwargs={"host": "0.0.0.0", "port": 8000},
        daemon=True
    ).start()
    print("🌐 API rodando na porta 8000!\n")

    await asyncio.Event().wait()

with client:
    client.loop.run_until_complete(main())