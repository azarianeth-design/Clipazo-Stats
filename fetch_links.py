"""
ClipAzo - Lector de enlaces de invitacion de Telegram.

Lee todos los enlaces de invitacion del grupo (los que ya tienes creados),
cuenta cuanta gente ha entrado por cada uno y escribe data.json.

Se ejecuta solo desde GitHub Actions. Variables de entorno necesarias:
    TG_API_ID       api_id de my.telegram.org
    TG_API_HASH     api_hash de my.telegram.org
    TG_SESSION      session string generada con get_session.py
    TG_CHAT         @usuario del grupo, o su id numerico (-100...)

Opcionales:
    MASK_LINKS      "1" (por defecto) publica el enlace censurado.
                    "0" publica el enlace completo.
    FETCH_DETAILS   "1" (por defecto) consulta la fecha de la ultima alta
                    de cada enlace. "0" va mas rapido y gasta menos API.
    INCLUDE_REVOKED "1" incluye tambien los enlaces revocados. Por defecto "0".
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

from telethon import TelegramClient, functions, types
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession

API_ID = int(os.environ["TG_API_ID"])
API_HASH = os.environ["TG_API_HASH"]
SESSION = os.environ["TG_SESSION"]
CHAT_RAW = os.environ["TG_CHAT"]

MASK_LINKS = os.environ.get("MASK_LINKS", "1") == "1"
FETCH_DETAILS = os.environ.get("FETCH_DETAILS", "0") == "1"
INCLUDE_REVOKED = os.environ.get("INCLUDE_REVOKED", "0") == "1"

OUTPUT = "data.json"
PAGE = 100
PAUSE = 0.4  # segundos entre llamadas, para no provocar limites de Telegram


def parse_chat(value):
    v = value.strip()
    if v.lstrip("-").isdigit():
        return int(v)
    return v


def iso(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return None


def mask(link):
    """t.me/+AbCdEfGhIjK  ->  t.me/+...GhIjK"""
    if not MASK_LINKS:
        return link
    tail = link[-5:]
    return f"t.me/+...{tail}"


async def with_retry(coro_factory, what):
    """Reintenta si Telegram nos frena."""
    for attempt in range(4):
        try:
            return await coro_factory()
        except FloodWaitError as e:
            wait = e.seconds + 2
            print(f"  Telegram pide esperar {wait}s ({what}). Esperando...")
            await asyncio.sleep(wait)
        except Exception as e:
            print(f"  Error en {what}: {type(e).__name__}: {e}")
            return None
    return None


async def get_admin_ids(client, chat):
    """Todos los administradores, para no perder enlaces creados por otros."""
    ids = []
    try:
        async for user in client.iter_participants(
            chat, filter=types.ChannelParticipantsAdmins
        ):
            ids.append(user.id)
    except Exception as e:
        print(f"  No se pudo listar administradores ({type(e).__name__}). Uso solo tu cuenta.")

    me = await client.get_me()
    if me.id not in ids:
        ids.insert(0, me.id)
    return ids


async def invites_of(client, chat, admin_id, revoked):
    """Todos los enlaces creados por un admin concreto, paginando."""
    found = []
    offset_date = None
    offset_link = None

    while True:
        res = await with_retry(
            lambda: client(
                functions.messages.GetExportedChatInvitesRequest(
                    peer=chat,
                    admin_id=admin_id,
                    limit=PAGE,
                    revoked=revoked,
                    offset_date=offset_date,
                    offset_link=offset_link,
                )
            ),
            f"enlaces de admin {admin_id}",
        )
        if res is None:
            break

        batch = [i for i in res.invites if isinstance(i, types.ChatInviteExported)]
        found.extend(batch)

        if len(batch) < PAGE:
            break

        offset_date = batch[-1].date
        offset_link = batch[-1].link
        await asyncio.sleep(PAUSE)

    return found


async def last_join(client, chat, link):
    """Fecha de la ultima persona que entro por este enlace, y total real."""
    res = await with_retry(
        lambda: client(
            functions.messages.GetChatInviteImportersRequest(
                peer=chat,
                link=link,
                offset_date=None,
                offset_user=types.InputUserEmpty(),
                limit=1,
            )
        ),
        "importers",
    )
    if res is None:
        return None, None

    fecha = iso(res.importers[0].date) if res.importers else None
    return res.count, fecha


async def main():
    chat_key = parse_chat(CHAT_RAW)

    client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
    await client.start()

    me = await client.get_me()
    print(f"Conectado como {me.first_name} (id {me.id})")

    chat = await client.get_entity(chat_key)
    titulo_grupo = getattr(chat, "title", str(chat_key))
    print(f"Grupo: {titulo_grupo}")

    admins = await get_admin_ids(client, chat)
    print(f"Administradores a revisar: {len(admins)}")

    crudos = {}
    for admin_id in admins:
        for inv in await invites_of(client, chat, admin_id, revoked=False):
            crudos[inv.link] = inv
        if INCLUDE_REVOKED:
            for inv in await invites_of(client, chat, admin_id, revoked=True):
                crudos[inv.link] = inv
        await asyncio.sleep(PAUSE)

    print(f"Enlaces encontrados: {len(crudos)}")

    enlaces = []
    for inv in crudos.values():
        altas = inv.usage or 0
        ultima = None

        if FETCH_DETAILS:
            real, ultima = await last_join(client, chat, inv.link)
            if real is not None:
                altas = real
            await asyncio.sleep(PAUSE)

        enlaces.append(
            {
                "titulo": inv.title or "(sin nombre)",
                "enlace": mask(inv.link),
                "altas": altas,
                "ultima_alta": ultima,
                "creado": iso(inv.date),
                "limite": inv.usage_limit,
                "pendientes": inv.requested or 0,
                "revocado": bool(inv.revoked),
            }
        )

    enlaces.sort(key=lambda x: x["altas"], reverse=True)

    salida = {
        "grupo": titulo_grupo,
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "total_altas": sum(e["altas"] for e in enlaces),
        "total_enlaces": len(enlaces),
        "enlaces": enlaces,
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"Escrito {OUTPUT}: {salida['total_altas']} altas en {len(enlaces)} enlaces")
    await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyError as e:
        print(f"Falta la variable de entorno {e}")
        sys.exit(1)
