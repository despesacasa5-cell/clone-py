from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import asyncio

async def clonar_grupo(client, origem_id, destino_id, mongo_uri, session_name):
    from mongo_session import load_last_message_id, save_last_message_id

    origem  = await client.get_entity(origem_id)
    destino = await client.get_entity(destino_id)

    # Busca o ID da última mensagem já clonada
    ultimo_id = load_last_message_id(mongo_uri, session_name)

    print(f"📤 Origem:  {origem.title}")
    print(f"📥 Destino: {destino.title}")
    print(f"🔖 Buscando mensagens após ID: {ultimo_id}\n")

    copiadas = 0
    erros = 0
    maior_id = ultimo_id  # vai atualizando conforme processa

    async for message in client.iter_messages(origem, min_id=ultimo_id, reverse=True):
        try:
            # Mensagem só de texto
            if message.text and not message.media:
                await client.send_message(destino, message.text)
                print(f"✅ Texto | ID {message.id}: {message.text[:50]}")
                copiadas += 1

            # Foto
            elif isinstance(message.media, MessageMediaPhoto):
                await client.send_file(
                    destino,
                    message.media,
                    caption=message.text or ''
                )
                print(f"🖼️ Foto  | ID {message.id}")
                copiadas += 1

            # Vídeo
            elif isinstance(message.media, MessageMediaDocument):
                mime = message.media.document.mime_type
                if 'video' in mime:
                    await client.send_file(
                        destino,
                        message.media,
                        caption=message.text or ''
                    )
                    print(f"🎥 Vídeo | ID {message.id}")
                    copiadas += 1

            # Atualiza o maior ID processado
            if message.id > maior_id:
                maior_id = message.id

            await asyncio.sleep(1.5)

        except Exception as e:
            erros += 1
            print(f"❌ Erro na mensagem {message.id}: {e}")
            await asyncio.sleep(3)

    # Salva o último ID no MongoDB só se processou algo novo
    if maior_id > ultimo_id:
        save_last_message_id(mongo_uri, session_name, maior_id)

    print(f"\n🏁 Concluído! ✅ Copiadas: {copiadas} | ❌ Erros: {erros}")

    if copiadas == 0:
        print("ℹ️ Nenhuma mensagem nova encontrada.")