import os
import random
import html
from collections import Counter, defaultdict, deque
from datetime import datetime

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from predict import analizar_texto

# ─── Configuración ──────────────────────────────────────

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ ERROR: Variable TELEGRAM_TOKEN no configurada")
    print("📌 Configuración:")
    print("   En PowerShell: $env:TELEGRAM_TOKEN='tu_token_aqui'")
    print("   En Linux/Mac:  export TELEGRAM_TOKEN='tu_token_aqui'")
    exit(1)

# Historial en memoria: últimos N análisis por usuario (se pierde al reiniciar el bot)
MAX_HISTORIAL = 20
HISTORIAL = defaultdict(lambda: deque(maxlen=MAX_HISTORIAL))

# ─── Datos ──────────────────────────────────────────────

# INTERPRETACIONES: Qué significa el mensaje que te enviaron
INTERPRETACIONES = {
    "reclamo": [
        "📢 La persona se siente ignorada y reclama tu atención.",
        "😤 Hay frustración porque esperaba una respuesta y no llegó.",
        "💢 Percibe que la estás descuidando o ignorando.",
    ],
    "celos": [
        "😒 Siente inseguridad y teme que haya un tercero.",
        "🔍 Necesita confirmar que sigue siendo importante para ti.",
        "🤨 Desconfía de tus acciones o amistades.",
    ],
    "agresion": [
        "⚠️ Está muy enojado y busca herir o provocar.",
        "🔥 El conflicto puede escalar si respondes de forma similar.",
        "💥 Hay agresividad que debes manejar con cuidado.",
    ],
    "tristeza": [
        "😢 Está pasando por un momento difícil o de dolor.",
        "🫂 Necesita apoyo emocional y contención.",
        "💔 Hay vulnerabilidad, no lo ignores.",
    ],
    "manipulacion": [
        "🎭 Está usando culpa o condiciones para obtener lo que quiere.",
        "⛓️ Quiere presionarte emocionalmente para que actúes.",
        "⚠️ Ten cuidado con responder desde la culpa.",
    ],
    "control": [
        "🔒 Quiere saber todo lo que haces y con quién.",
        "👁️ Hay una necesidad excesiva de controlarte.",
        "📱 No confía plenamente en ti.",
    ],
    "ruptura": [
        "💔 Está considerando seriamente terminar la relación.",
        "😩 Hay agotamiento emocional acumulado.",
        "🚪 Quiere distancia o poner un punto final.",
    ],
    "desinteres": [
        "😐 No muestra interés en seguir la conversación.",
        "❄️ Hay distancia emocional o está ocupado.",
        "📉 Probablemente no quiere profundizar.",
    ],
    "inseguridad": [
        "😟 Tiene dudas sobre la relación o sobre sí mismo.",
        "🤔 Necesita reafirmación y seguridad.",
        "🌀 Busca calmar su ansiedad con respuestas claras.",
    ],
    "afecto": [
        "💕 Está expresando cariño y buenos sentimientos.",
        "🤗 Quiere acercarse y fortalecer el vínculo.",
        "🌸 Hay conexión emocional positiva.",
    ],
    "curiosidad": [
        "🤔 Tiene interés genuino en ti y tu vida.",
        "💬 Quiere iniciar o mantener una conversación.",
        "🔍 Busca conocer más sobre ti.",
    ],
    "normal": [
        "💬 Es una conversación cotidiana sin carga emocional.",
        "✅ No hay señales de conflicto ni urgencia.",
        "📝 Todo fluye con normalidad.",
    ],
}

# SUGERENCIAS: Cómo responder al mensaje (para TI)
SUGERENCIAS = {
    "reclamo": [
        "🗣️ Responde: 'Entiendo que te sientes ignorado, no fue mi intención. Hablemos.'",
        "⏸️ Reconoce su molestia antes de dar explicaciones: 'Tienes razón, no respondí rápido.'",
        "🤝 Pregunta: '¿Qué puedo hacer para que no te sientas así?'",
    ],
    "celos": [
        "🧠 Responde con calma: 'No hay nadie más, pero entiendo tu inseguridad.'",
        "💬 Valida su emoción: 'Veo que esto te preocupa, hablemos sin pelear.'",
        "🔐 Reafirma: 'Eres importante para mí. ¿Podemos hablar de esto tranquilos?'",
    ],
    "agresion": [
        "🌬️ No respondas con agresión. Di: 'Esto se está poniendo feo, hablemos más tarde.'",
        "🚫 Establece límite: 'No voy a responder si me hablas así.'",
        "⏰ Tómate un tiempo: 'Mejor hablamos cuando estemos más calmados.'",
    ],
    "tristeza": [
        "👥 Responde: 'Estoy aquí para ti. ¿Quieres hablar de lo que pasa?'",
        "💬 Muestra apoyo: 'Lamento que te sientas así, cuentas conmigo.'",
        "🤗 Ofrece compañía: '¿Necesitas desahogarte o prefieres distraerte?'",
    ],
    "manipulacion": [
        "🚩 No cedas por culpa. Di: 'No me gusta que me condiciones así.'",
        "🗣️ Marca límite: 'Si me quieres pedir algo, hazlo sin chantajes.'",
        "⚖️ Responde neutro: 'Te escucho, pero no voy a reaccionar desde la culpa.'",
    ],
    "control": [
        "🤝 Responde: 'Confío en ti y espero que tú confíes en mí.'",
        "📱 Marca espacio: 'Está bien que quieras saber, pero también necesito mi espacio.'",
        "🧘 Tranquiliza: 'No pasa nada, pero no puedo responder todo el tiempo.'",
    ],
    "ruptura": [
        "💬 Responde: 'Hablemos esto en persona, es importante.'",
        "🤔 Pide tiempo: 'No tomemos decisiones en caliente. Hablemos mañana.'",
        "🕊️ Si es firme: 'Lo respeto si es tu decisión, pero me duele.'",
    ],
    "desinteres": [
        "🧐 Pregunta: '¿Estás bien? Parece que no tienes ganas de hablar.'",
        "💬 Dale espacio: 'Cuando quieras hablar, aquí estoy.'",
        "⏸️ No insistas: 'Ok, hablamos cuando tengas tiempo.'",
    ],
    "inseguridad": [
        "🔍 Responde: 'Estoy contigo, no tienes nada que temer.'",
        "💬 Tranquiliza: 'Si algo te preocupa, pregúntame sin miedo.'",
        "📖 Reafirma: 'Me importas y no tengo nada que ocultar.'",
    ],
    "afecto": [
        "🌸 Corresponde: 'Yo también te quiero mucho ❤️'",
        "💌 Agradece: 'Qué bonito mensaje, gracias por tus palabras.'",
        "🎁 Sorprende: 'Me hiciste el día, te quiero igual.'",
    ],
    "curiosidad": [
        "🔍 Responde con entusiasmo: 'Todo bien, ¿y tú? Cuéntame.'",
        "💬 Aprovecha: 'Justo pensaba en ti. ¿Qué has hecho?'",
        "🌟 Sigue la conversación: 'Me alegra que preguntes, te cuento...'",
    ],
    "normal": [
        "👍 Responde con naturalidad: 'Todo bien, ¿y tú?'",
        "💬 Sigue la conversación: 'Qué bueno, seguimos hablando.'",
        "🌟 Mantén el tono: 'Genial, cualquier cosa me dices.'",
    ],
}

EMOJIS = {
    "reclamo": "😔",
    "celos": "😒",
    "agresion": "⚠️",
    "tristeza": "😢",
    "manipulacion": "🚩",
    "control": "🔒",
    "ruptura": "💔",
    "desinteres": "😶",
    "inseguridad": "😟",
    "afecto": "💕",
    "curiosidad": "🤔",
    "normal": "💬",
}

EMOJIS_EMOCION = {
    "positivo": "😊",
    "tristeza": "😢",
    "enojo": "😠",
    "sorpresa": "😲",
    "disgusto": "😖",
    "miedo": "😨",
    "neutral": "😐",
}

# ─── Funciones auxiliares ───────────────────────────────

def construir_barra(valor: int) -> str:
    bloques = valor // 10
    return "█" * bloques + "░" * (10 - bloques)

def obtener_texto(diccionario, clave, default="normal"):
    return random.choice(diccionario.get(clave, diccionario[default]))

def formatear_respuesta(datos: dict) -> str:
    return (
        f"{datos['emoji_principal']} *Análisis del mensaje que te enviaron*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{datos['emoji_emocion']} *Emoción detectada:* {datos['emocion']}\n"
        f"🚩 *Toxicidad:* {datos['toxicidad']}\n"
        f"🧠 *Intención:* {datos['intencion']}\n"
        f"💔 *Ghosting:* {datos['ghosting_bar']} {datos['ghosting']}%\n"
        f"🔥 *Riesgo:* {datos['riesgo']}\n"
        f"🎯 *Confianza del modelo:* {datos['confianza']}%\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Qué significa:*\n{datos['interpretacion']}\n\n"
        f"💬 *Cómo responder:*\n{datos['sugerencia']}"
    )

# ─── Handler principal ──────────────────────────────────

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        texto = update.message.text
        
        emocion, toxicidad, ghosting, riesgo, intencion, confianza = analizar_texto(texto)
        
        datos = {
            "emoji_principal": EMOJIS.get(intencion, "💬"),
            "emoji_emocion": EMOJIS_EMOCION.get(emocion, "😐"),
            "emocion": emocion.capitalize(),
            "toxicidad": "🔴 Alta" if toxicidad == "si" else "🟢 Baja",
            "intencion": intencion.capitalize(),
            "ghosting": ghosting,
            "ghosting_bar": construir_barra(ghosting),
            "riesgo": riesgo,
            "interpretacion": obtener_texto(INTERPRETACIONES, intencion),
            "sugerencia": obtener_texto(SUGERENCIAS, intencion),
            "confianza": confianza,
        }

        HISTORIAL[update.effective_user.id].append({
            "hora": datetime.now().strftime("%H:%M"),
            "texto": texto,
            "emocion": emocion,
            "intencion": intencion,
            "toxico": toxicidad == "si",
            "ghosting": ghosting,
            "riesgo": riesgo,
        })
        
        respuesta = formatear_respuesta(datos)
        await update.message.reply_text(respuesta, parse_mode="Markdown")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        await update.message.reply_text("⚠️ Ocurrió un error al procesar el mensaje.")

# ─── Comandos (agregado) ────────────────────────────────

TEXTO_AYUDA = (
    "🤖 <b>Chat Analyzer Bot</b>\n\n"
    "Reenvíame o escribe un mensaje que te hayan enviado y te digo qué emoción, "
    "intención y riesgo tiene, y cómo podrías responder.\n\n"
    "<b>Comandos</b>\n"
    "/start – Bienvenida\n"
    "/ayuda – Esta ayuda\n"
    f"/historial – Tus últimos {MAX_HISTORIAL} mensajes analizados\n"
    "/resumen – Evolución emocional de la conversación\n"
    "/consejo – Consejo según tu conversación (o /consejo &lt;mensaje&gt;)\n"
    "/borrar – Borra tu historial"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = html.escape(update.effective_user.first_name or "")
    await update.message.reply_text(f"👋 ¡Hola {nombre}!\n\n" + TEXTO_AYUDA, parse_mode="HTML")


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(TEXTO_AYUDA, parse_mode="HTML")


async def cmd_historial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registros = HISTORIAL[update.effective_user.id]
    if not registros:
        await update.message.reply_text("📭 Aún no has analizado mensajes. Envíame uno.")
        return
    lineas = ["🗂️ <b>Tu historial</b>\n"]
    for i, r in enumerate(registros, 1):
        texto = r["texto"] if len(r["texto"]) <= 40 else r["texto"][:37] + "..."
        lineas.append(
            f"{i}. <code>{r['hora']}</code> {EMOJIS_EMOCION.get(r['emocion'], '😐')} "
            f"{EMOJIS.get(r['intencion'], '💬')} <i>{html.escape(texto)}</i> → "
            f"{r['intencion']} · {r['riesgo']}"
        )
    await update.message.reply_text("\n".join(lineas), parse_mode="HTML")


def tendencia(registros) -> str:
    """Compara el ghosting medio de la primera y la segunda mitad del historial."""
    if len(registros) < 4:
        return "➖ Se necesitan al menos 4 mensajes para ver una tendencia."
    mitad = len(registros) // 2
    lista = list(registros)
    antes = sum(r["ghosting"] for r in lista[:mitad]) / mitad
    despues = sum(r["ghosting"] for r in lista[mitad:]) / (len(lista) - mitad)
    if despues - antes > 10:
        return "📉 La conversación se está enfriando: aumentan las señales de distancia."
    if antes - despues > 10:
        return "📈 La conversación se está calentando: hay más interés que antes."
    return "➖ El tono se mantiene estable."


async def cmd_resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registros = HISTORIAL[update.effective_user.id]
    if not registros:
        await update.message.reply_text("📭 Aún no has analizado mensajes. Envíame uno.")
        return

    total = len(registros)
    emociones = Counter(r["emocion"] for r in registros)
    intenciones = Counter(r["intencion"] for r in registros)
    toxicos = sum(r["toxico"] for r in registros)
    altos = sum(r["riesgo"].endswith("Alto") for r in registros)
    ghosting_medio = round(sum(r["ghosting"] for r in registros) / total)

    lineas = [f"📊 <b>Resumen de {total} mensaje(s)</b>", "━━━━━━━━━━━━━━━━━━━━", "<b>Emociones</b>"]
    for emo, n in emociones.most_common():
        pct = round(n * 100 / total)
        lineas.append(f"{EMOJIS_EMOCION.get(emo, '😐')} {emo.capitalize():<9} {construir_barra(pct)} {pct}%")
    lineas.append("\n<b>Intenciones más frecuentes</b>")
    for inten, n in intenciones.most_common(3):
        lineas.append(f"{EMOJIS.get(inten, '💬')} {inten.capitalize()}: {n}")
    lineas += [
        "",
        f"🚩 Mensajes tóxicos: {toxicos}",
        f"🔴 Mensajes de riesgo alto: {altos}",
        f"💔 Ghosting promedio: {construir_barra(ghosting_medio)} {ghosting_medio}%",
        "",
        tendencia(registros),
    ]
    if altos >= 2 or intenciones["control"] + intenciones["manipulacion"] >= 2:
        lineas.append(
            "\n⚠️ Se repiten señales de control, manipulación o agresión. "
            "Si te sientes inseguro/a en esta relación, habla con alguien de confianza."
        )
    await update.message.reply_text("\n".join(lineas), parse_mode="HTML")


# ─── Función nueva: /consejo ────────────────────────────

CONSEJOS = {
    "agresion": "🛑 Hay agresividad en la conversación. No respondas en caliente: pon un límite claro y retoma cuando ambos estén calmados. Nadie merece insultos.",
    "control": "🔒 Se repiten señales de control (ubicación, con quién hablas). Una relación sana se basa en la confianza: está bien pedir tu espacio.",
    "manipulacion": "🎭 Aparecen frases de culpa o condiciones. Escucha, pero no tomes decisiones desde la culpa; expresa lo que sientes con calma.",
    "celos": "😒 Hay inseguridad y celos. Hablen de lo que la causa sin acusarse y acuerden qué necesita cada uno para sentirse tranquilo.",
    "reclamo": "📢 La otra persona siente que no le prestas atención. Reconoce su molestia y acuerden cómo comunicarse cuando estén ocupados.",
    "ruptura": "💔 Se habla de terminar. Es mejor conversarlo en persona, sin prisas, y respetar la decisión del otro aunque duela.",
    "desinteres": "❄️ Las respuestas son cortas y frías. Pregunta directamente si todo está bien y, si no hay interés, no insistas: dale espacio.",
    "inseguridad": "😟 La otra persona necesita sentirse segura. Pequeños gestos de cariño y respuestas claras ayudan mucho.",
    "tristeza": "🫂 La otra persona está pasando por un momento difícil. Más que soluciones, ofrece escucha y compañía.",
    "afecto": "💕 La conversación va muy bien, hay cariño. Sigue correspondiendo y demuestra interés también con hechos.",
    "curiosidad": "🤔 Hay interés en conocerte. Aprovecha para hacer preguntas tú también y mantener la conversación viva.",
    "normal": "💬 Es una conversación tranquila. Mantén el tono natural y cercano.",
}

# Prioridad: si aparece algo grave, el consejo se centra en eso aunque no sea lo más frecuente
PRIORIDAD = ["agresion", "control", "manipulacion", "ruptura", "celos", "reclamo",
             "tristeza", "inseguridad", "desinteres", "afecto", "curiosidad", "normal"]


def elegir_consejo(registros) -> str:
    """Arma un consejo a partir del historial de mensajes analizados."""
    intenciones = Counter(r["intencion"] for r in registros)
    graves = [i for i in PRIORIDAD[:4] if intenciones[i] > 0]
    principal = graves[0] if graves else intenciones.most_common(1)[0][0]

    partes = [CONSEJOS.get(principal, CONSEJOS["normal"])]

    toxicos = sum(r["toxico"] for r in registros)
    if toxicos:
        partes.append(f"🚩 {toxicos} mensaje(s) fueron tóxicos. Protege tu bienestar: no tienes que tolerar faltas de respeto.")

    ghosting = round(sum(r["ghosting"] for r in registros) / len(registros))
    if ghosting >= 50:
        partes.append(f"💔 El ghosting promedio es alto ({ghosting}%). Si siempre eres tú quien busca la conversación, quizá toque bajar la intensidad.")

    if len(registros) >= 4:
        partes.append(tendencia(registros))

    return "\n\n".join(partes)


async def cmd_consejo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Opción 1: /consejo <mensaje>  → consejo para ese mensaje concreto
    if context.args:
        texto = " ".join(context.args)
        emocion, toxicidad, ghosting, riesgo, intencion, confianza = analizar_texto(texto)
        registro = {"intencion": intencion, "toxico": toxicidad == "si", "ghosting": ghosting}
        consejo = elegir_consejo([registro])
        await update.message.reply_text(
            f"🧭 <b>Consejo para:</b> <i>{html.escape(texto)}</i>\n"
            f"🧠 Intención: {intencion.capitalize()} · 🔥 Riesgo: {riesgo}\n\n{consejo}",
            parse_mode="HTML",
        )
        return

    # Opción 2: /consejo  → consejo según todo el historial
    registros = HISTORIAL[update.effective_user.id]
    if not registros:
        await update.message.reply_text(
            "📭 Aún no has analizado mensajes.\n"
            "Envíame algunos mensajes primero, o usa: /consejo <mensaje>"
        )
        return
    await update.message.reply_text(
        f"🧭 <b>Consejo según tus últimos {len(registros)} mensaje(s)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n{elegir_consejo(registros)}",
        parse_mode="HTML",
    )

async def cmd_borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    HISTORIAL.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑️ Historial borrado.")

# ─── Inicialización ─────────────────────────────────────

def main():
    print("🤖 Bot de análisis de mensajes activo...")
    print("📌 Analizo los mensajes que TE ENVÍAN y te digo cómo responder")
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler(["ayuda", "help"], cmd_ayuda))
    app.add_handler(CommandHandler("historial", cmd_historial))
    app.add_handler(CommandHandler("resumen", cmd_resumen))
    app.add_handler(CommandHandler("borrar", cmd_borrar))
    app.add_handler(CommandHandler("consejo", cmd_consejo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    
    print("🟢 Bot corriendo... Esperando mensajes")
    app.run_polling()

if __name__ == "__main__":
    main()