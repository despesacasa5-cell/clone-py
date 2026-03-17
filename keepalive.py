import asyncio
import state

async def keepalive():
    """Verifica conexão a cada 5 minutos e reconecta se necessário"""
    while True:
        try:
            client = state.telegram_client
            if client:
                if not client.is_connected():
                    print("⚠️ Telegram desconectado! Reconectando...")
                    await client.connect()
                    print("✅ Reconectado!")
                else:
                    # Mantém a conexão viva com um ping
                    await client.get_me()
        except Exception as e:
            print(f"❌ Erro no keepalive: {e}")
            try:
                await state.telegram_client.connect()
            except Exception as e2:
                print(f"❌ Falha ao reconectar: {e2}")

        await asyncio.sleep(300)  # verifica a cada 5 minutos