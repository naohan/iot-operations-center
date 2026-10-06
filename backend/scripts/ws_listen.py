"""
Cliente de prueba WebSocket (Etapa 3).

Uso (con la API levantada):
    python scripts/ws_listen.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import websockets


async def listen(url: str, max_messages: int | None) -> None:
    print(f"Conectando a {url} ...", flush=True)
    async with websockets.connect(url) as ws:
        print("Conectado. Esperando eventos (Ctrl+C para salir)...\n", flush=True)
        count = 0
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                print(raw, flush=True)
                continue

            event_type = msg.get("type", "?")
            data = msg.get("data", {})
            if event_type == "measurement":
                print(
                    f"📡 measurement | {data.get('device_code')} "
                    f"T={data.get('temperature')} H={data.get('humidity')} P={data.get('pressure')}",
                    flush=True,
                )
            elif event_type == "alert":
                print(
                    f"⚠  alert       | {data.get('device_code')} "
                    f"[{data.get('severity')}] {data.get('message')}",
                    flush=True,
                )
            elif event_type == "device_status":
                print(
                    f"🔌 status      | {data.get('device_code')} → {data.get('status')}",
                    flush=True,
                )
            elif event_type == "connected":
                print(f"✅ connected   | clientes={data.get('clients')}", flush=True)
            else:
                print(f"• {event_type}: {data}", flush=True)

            count += 1
            if max_messages is not None and count >= max_messages:
                break


def main() -> int:
    parser = argparse.ArgumentParser(description="Escucha el hub WebSocket de la API")
    parser.add_argument("--url", default="ws://localhost:8000/ws")
    parser.add_argument("--max", type=int, default=None, help="Salir tras N mensajes")
    args = parser.parse_args()
    try:
        asyncio.run(listen(args.url, args.max))
    except KeyboardInterrupt:
        print("\nDetenido")
    return 0


if __name__ == "__main__":
    sys.exit(main())
