from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import asyncio

async def clonar_grupo(client, pair_name, origem_id, destino_id, mongo_uri):
    from mongo_session import load_last_message_id, save_last_message_id

    origem  = await client.get_entity(origem_id)
    destino = await client.get_entity(destino_id)

    ultimo_id = load_last_message_id(mongo_uri, pair_name)

    print(f"\n🔁 [{pair_name}] {origem.title} → {destino.title}")
    print(f"🔖 Buscando mensagens após ID: {ultimo_id}")

    copiadas = 0
    erros = 0
    maior_id = ultimo_id

    async for message in client.iter_messages(origem, min_id=ultimo_id, reverse=True):
        try:
            if message.text and not message.media:
                await client.send_message(destino, message.text)
                copiadas += 1

            elif isinstance(message.media, MessageMediaPhoto):
                await client.send_file(destino, message.media, caption=message.text or '')
                copiadas += 1

            elif isinstance(message.media, MessageMediaDocument):
                if 'video' in message.media.document.mime_type:
                    await client.send_file(destino, message.media, caption=message.text or '')
                    copiadas += 1

            if message.id > maior_id:
                maior_id = message.id

            await asyncio.sleep(1.5)

        except Exception as e:
            erros += 1
            print(f"❌ Erro na mensagem {message.id}: {e}")
            await asyncio.sleep(3)

    if maior_id > ultimo_id:
        save_last_message_id(mongo_uri, pair_name, maior_id)

    # Retorna resumo
    return {
        "copiadas": copiadas,
        "erros": erros,
        "ultimo_id_anterior": ultimo_id,
        "ultimo_id_atual": maior_id
    }