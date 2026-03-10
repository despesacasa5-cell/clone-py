from telethon.tl.types import User, Chat, Channel
from mongo_session import save_dialogs

async def listar_e_salvar_dialogs(client, mongo_uri):
    """Lista todos os diálogos e salva no MongoDB"""
    print("🔍 Buscando diálogos...")

    dialogs = []

    async for dialog in client.iter_dialogs():
        entity = dialog.entity

        if isinstance(entity, User):
            tipo = 'privado'
        elif isinstance(entity, Chat):
            tipo = 'grupo'
        elif isinstance(entity, Channel):
            tipo = 'canal' if entity.broadcast else 'supergrupo'
        else:
            tipo = 'desconhecido'

        dialogs.append({
            'id': dialog.id,
            'name': dialog.name,
            'type': tipo
        })

        print(f"{'👤' if tipo == 'privado' else '👥' if tipo == 'grupo' else '📢' if tipo == 'canal' else '💬'} {tipo.upper()} | ID: {dialog.id} | {dialog.name}")

    save_dialogs(mongo_uri, dialogs)
    return dialogs