"""
ClipAzo - Te dice el ID de tus grupos (para rellenar TG_CHAT).

Uso:
    python list_chats.py
Te pide api_id, api_hash y la session string que sacaste con get_session.py.
"""

from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("api_id: ").strip())
api_hash = input("api_hash: ").strip()
session = input("session string: ").strip()

with TelegramClient(StringSession(session), api_id, api_hash) as client:
    print()
    print(f"{'ID':>16}  {'TIPO':<10} NOMBRE")
    print("-" * 70)
    for d in client.iter_dialogs():
        if d.is_group or d.is_channel:
            tipo = "canal" if d.is_channel and not d.is_group else "grupo"
            print(f"{d.id:>16}  {tipo:<10} {d.name}")
    print()
    print("Copia el ID de tu grupo (con el signo menos incluido) en TG_CHAT.")
