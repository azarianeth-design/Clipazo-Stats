"""
ClipAzo - Generador de session string (SE EJECUTA UNA SOLA VEZ, EN TU ORDENADOR)

Uso:
    pip install telethon
    python get_session.py

Te pedira tu api_id, tu api_hash y tu telefono. Telegram te mandara un codigo
por la propia app. Al final te imprime una cadena larga: esa es tu SESSION.

IMPORTANTE: esa cadena da acceso completo a tu cuenta de Telegram.
No la subas al repositorio, no la pegues en un chat. Solo va en los
Secrets de GitHub.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

print("=" * 60)
print("  ClipAzo - generador de session string")
print("=" * 60)
print()
print("Saca tu api_id y api_hash en https://my.telegram.org")
print("  -> API development tools")
print()

api_id = int(input("api_id: ").strip())
api_hash = input("api_hash: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    me = client.get_me()
    print()
    print(f"Conectado como: {me.first_name} (@{me.username})")
    print()
    print("-" * 60)
    print("TU SESSION STRING (copiala entera, es una sola linea):")
    print("-" * 60)
    print()
    print(client.session.save())
    print()
    print("-" * 60)
    print("Guardala en GitHub -> Settings -> Secrets -> TG_SESSION")
    print("Y luego borra esto de la pantalla. No la compartas con nadie.")
    print("-" * 60)
