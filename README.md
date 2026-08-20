# ClipAzo · Ranking de clippers

Página web que muestra cuánta gente ha entrado al grupo de Telegram por cada
enlace de invitación. Lee los enlaces que **ya tienes creados**. Coste: 0 €/mes.

---

## Qué hay aquí

| Archivo | Para qué sirve |
|---|---|
| `get_session.py` | Lo ejecutas **una sola vez en tu ordenador**. Genera la llave de acceso. |
| `list_chats.py` | Te dice el ID de tu grupo. También una sola vez. |
| `fetch_links.py` | El que hace el trabajo. Lo lanza GitHub solo, tú no lo tocas. |
| `index.html` | La página web. |
| `.github/workflows/actualizar.yml` | El reloj: ejecuta el script cada 15 minutos. |
| `data.json` | Los datos. Se regenera solo. |

---

## Montaje, paso a paso

### 1. Saca tus credenciales de Telegram

Entra en **https://my.telegram.org** → *API development tools*. Rellena el
formulario (el nombre de la app da igual, pon `clipazo`). Te da dos cosas:
`api_id` (un número) y `api_hash` (una cadena larga). Guárdalos.

### 2. Genera tu session string

En tu ordenador, con Python instalado:

```bash
pip install telethon
python get_session.py
```

Te pide el `api_id`, el `api_hash` y tu teléfono. Telegram te manda un código
por la app. Al final imprime una cadena larguísima: **esa es tu session
string**. Cópiala.

> ⚠️ Esa cadena da acceso completo a tu cuenta de Telegram. No la subas a
> ningún archivo, no la pegues en ningún chat. Solo va en los Secrets de GitHub.

### 3. Saca el ID del grupo

```bash
python list_chats.py
```

Te lista tus grupos con su ID. Copia el del grupo de clipping, con el signo
menos incluido (algo tipo `-1001234567890`).

### 4. Sube esto a GitHub

Crea un repositorio **público** nuevo (público para que Pages sea gratis) y
sube todos estos archivos. La session string no está en ninguno de ellos, así
que no hay problema en que el repo sea público.

### 5. Mete los secrets

En el repo: **Settings → Secrets and variables → Actions → New repository
secret**. Crea estos cuatro:

| Nombre | Valor |
|---|---|
| `TG_API_ID` | el número del paso 1 |
| `TG_API_HASH` | la cadena del paso 1 |
| `TG_SESSION` | la session string del paso 2 |
| `TG_CHAT` | el ID del grupo del paso 3 |

### 6. Enciende la web

**Settings → Pages → Source: Deploy from a branch → main / (root) → Save.**
En un par de minutos te da la URL: `https://TUUSUARIO.github.io/NOMBREDELREPO/`

### 7. Primera ejecución

Pestaña **Actions** → *Actualizar datos de ClipAzo* → botón **Run workflow**.
Tarda menos de un minuto. Recarga la página y ya tienes los datos.

A partir de ahí se actualiza solo cada 15 minutos.

---

## Ajustes

Se cambian en el bloque `env:` del archivo `.github/workflows/actualizar.yml`:

- `MASK_LINKS: "1"` → publica el enlace censurado (`t.me/+...GhIjK`). Ponlo a
  `"0"` si quieres que se vea entero. Recomendado dejarlo en `"1"`: si no,
  cualquiera puede coger el enlace de otro clipper.
- `FETCH_DETAILS: "0"` → por defecto apagado. El contador de altas sale del
  propio campo de Telegram (el mismo número que ves en la app), que es
  instantáneo. Si lo pones a `"1"`, además consulta la fecha de la última alta
  de cada enlace para rellenar la columna "Última" — pero hace una llamada
  extra por enlace, así que con muchos enlaces va lento y arriesga límites.
- `INCLUDE_REVOKED: "1"` → incluye también enlaces revocados. Por defecto no.

Para cambiar cada cuánto se actualiza, toca el `cron`. **No bajes de 15
minutos** o Telegram empieza a limitarte.

---

## Cosas que conviene saber

- **GitHub apaga los cron a los 60 días** si no hay actividad humana en el
  repo. Entra de vez en cuando y toca algo, o el día menos pensado deja de
  actualizarse en silencio.
- Los cron de GitHub Actions **no son puntuales**: pueden retrasarse unos
  minutos cuando hay mucha carga. Da igual para esto.
- La página es **pública**: todos los clippers ven los números de todos. Es lo
  normal en clipping y suele funcionar como motivación, pero tenlo claro.
- El nombre que se muestra en el ranking es el **título del enlace** en
  Telegram. Si tus enlaces no tienen título, edítalos en la app y ponles el
  nombre del clipper — es lo que va a salir en la web.
