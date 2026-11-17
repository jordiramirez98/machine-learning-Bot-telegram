# probar.py - Prueba el bot en la terminal, sin Telegram ni token.
# Uso:  python probar.py
import asyncio
import os
import re
import sys
from types import SimpleNamespace

# La consola de Windows a veces no muestra emojis: se fuerza UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

os.environ.setdefault("TELEGRAM_TOKEN", "modo-prueba")  # bot.py exige que exista
import bot  # noqa: E402


def limpiar(texto: str) -> str:
    """Quita el formato de Telegram (HTML / Markdown) para leerlo en la consola."""
    texto = re.sub(r"</?(b|i|code)>", "", texto)
    texto = texto.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return texto.replace("*", "")


class MensajeFalso:
    def __init__(self, texto):
        self.text = texto

    async def reply_text(self, texto, parse_mode=None):
        print("\n🤖 Bot:\n" + limpiar(texto) + "\n")


COMANDOS = {
    "/start": bot.cmd_start,
    "/ayuda": bot.cmd_ayuda,
    "/help": bot.cmd_ayuda,
    "/historial": bot.cmd_historial,
    "/resumen": bot.cmd_resumen,
    "/consejo": bot.cmd_consejo,
    "/borrar": bot.cmd_borrar,
}


async def main():
    usuario = SimpleNamespace(id=1, first_name="Tester")
    print("\n💬 MODO PRUEBA – escribe mensajes como si te los hubieran enviado.")
    print("   Comandos: /start /historial /resumen /consejo /borrar   ·   'salir' para terminar\n")

    while True:
        try:
            texto = input("🧑 Tú: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not texto:
            continue
        if texto.lower() in ("salir", "exit", "/salir"):
            break

        update = SimpleNamespace(message=MensajeFalso(texto), effective_user=usuario)
        if texto.startswith("/"):
            nombre, *args = texto.split()
            funcion = COMANDOS.get(nombre.lower())
            if funcion is None:
                print("\n⚠️ Comando no reconocido. Usa /ayuda\n")
                continue
            await funcion(update, SimpleNamespace(args=args))
        else:
            await bot.responder(update, None)

    print("\n👋 Fin del modo prueba.")


if __name__ == "__main__":
    asyncio.run(main())
