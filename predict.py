# predict.py - Motor de análisis (pysentimiento 0.7.x + reglas)
import re
import unicodedata

from pysentimiento import create_analyzer

# ─── Modelos preentrenados ─────────────────────────

print("🔄 Cargando modelos de pysentimiento...")
emotion_analyzer = create_analyzer(task="emotion", lang="es")
hate_analyzer = create_analyzer(task="hate_speech", lang="es")
print("✅ Modelos cargados correctamente")

# ─── Utilidades de texto ──────────────────────────────

def normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para que 'por que' y 'por qué' coincidan."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def contiene(texto: str, frases) -> bool:
    """Busca frases completas (no subcadenas): 'ya' no coincide con 'playa'."""
    return any(re.search(rf"(?<!\w){re.escape(f)}(?!\w)", texto) for f in frases)

# ─── Intención (reglas) ───────────────────────────────
# El orden importa: se evalúa de arriba hacia abajo y gana la primera regla.

REGLAS_INTENCION = [
    ("agresion", ["odio", "estupido", "estupida", "idiota", "imbecil", "mierda",
                  "que asco", "callate", "inutil", "maldito", "maldita"]),
    ("ruptura", ["terminar", "terminemos", "te dejo", "dejarte", "no quiero seguir",
                 "se acabo", "hasta aqui", "se termino", "ya no te quiero"]),
    ("manipulacion", ["si me quisieras", "si realmente me quisieras", "deberias",
                      "nunca haces", "siempre igual", "como siempre", "por tu culpa",
                      "despues de todo lo que hice"]),
    ("control", ["donde estas", "con quien hablas", "dime la verdad", "ubicacion",
                 "envia ubicacion", "pasame tu clave", "dame tu contrasena",
                 "muestrame tu celular"]),
    ("celos", ["con quien", "quien es", "te vi con", "te veo con", "andabas con",
               "quien te escribio", "quien te habla"]),
    ("reclamo", ["por que no respondes", "por que no me respondes", "me ignoras",
                 "no contestas", "no me contestas", "por que tardas", "por que demoras",
                 "no me escribes", "me dejaste en visto"]),
    ("inseguridad", ["me quieres", "todavia me quieres", "aun me quieres",
                     "estas seguro", "estas segura", "te aburri", "soy suficiente",
                     "me vas a dejar"]),
    ("afecto", ["te quiero", "te amo", "me gustas", "te extrano", "te necesito",
                "te adoro", "mi amor", "eres lo mejor"]),
    ("tristeza", ["triste", "deprimido", "deprimida", "me siento mal", "estoy mal",
                  "solo", "sola", "soledad", "llorar", "llorando"]),
    ("curiosidad", ["que tal", "como estas", "que haces", "como te va", "en que andas",
                    "que cuentas", "como te fue"]),
    ("desinteres", ["ok", "okay", "vale", "ah", "ya", "como digas", "da igual",
                    "me da igual", "jaja", "jeje", "k", "mmm", "aja"]),
]


def detectar_intencion(texto: str) -> str:
    t = normalizar(texto)
    for intencion, frases in REGLAS_INTENCION:
        if contiene(t, frases):
            # Palabras de desinterés solo cuentan si el mensaje es muy corto
            if intencion == "desinteres" and len(t.split()) > 3:
                continue
            return intencion
    return "normal"

# ─── Ghosting ─────────────────────────────────────────

PALABRAS_DISTANCIA = ["ok", "vale", "ah", "ya", "luego", "ocupado", "ocupada",
                      "ahora no", "despues", "manana", "ahora no puedo", "otro dia"]


def calcular_ghosting(texto, intencion, emocion):
    score = 0
    t = normalizar(texto)

    if len(t) <= 5:
        score += 35
    if len(t.split()) == 1:
        score += 25
    if contiene(t, PALABRAS_DISTANCIA):
        score += 30

    if intencion == "desinteres":
        score += 35
    elif intencion == "reclamo":
        score += 15
    elif intencion in ("afecto", "curiosidad"):
        score -= 25

    if emocion in ["sadness", "anger", "fear", "disgust"]:
        score += 10
    elif emocion in ["joy", "surprise"]:
        score -= 15

    return max(0, min(score, 95))

# ─── Toxicidad / riesgo ───────────────────────────────

def es_toxico(hate_result) -> bool:
    """hate_speech en pysentimiento es multi-etiqueta: output es una lista
    (p. ej. ['hateful', 'targeted']). Se acepta también un string por compatibilidad."""
    salida = hate_result.output
    if isinstance(salida, str):
        salida = [salida]
    return any(e in ("hateful", "targeted", "aggressive") for e in salida)


def calcular_riesgo(toxico, intencion, emocion):
    if toxico or intencion in ["agresion", "control"]:
        return "🔴 Alto"
    if intencion in ["celos", "reclamo", "ruptura", "manipulacion"]:
        return "🟡 Medio"
    if emocion in ["anger", "disgust"]:
        return "🟡 Medio"
    return "🟢 Bajo"

# ─── Mapear emociones ─────────────────────────────────

EMOCION_MAP = {
    "joy": "positivo",
    "sadness": "tristeza",
    "anger": "enojo",
    "surprise": "sorpresa",
    "disgust": "disgusto",
    "fear": "miedo",
    "others": "neutral",
    "neutral": "neutral",
}


def mapear_emocion(emocion_raw):
    return EMOCION_MAP.get(emocion_raw, "neutral")

# ─── Función principal ────────────────────────────────

def analizar_texto(texto):
    try:
        emocion_pred = emotion_analyzer.predict(texto)
        hate_pred = hate_analyzer.predict(texto)

        emocion_raw = emocion_pred.output
        emocion = mapear_emocion(emocion_raw)

        intencion = detectar_intencion(texto)
        toxico = es_toxico(hate_pred) or intencion == "agresion"
        toxicidad = "si" if toxico else "no"

        ghosting = calcular_ghosting(texto, intencion, emocion_raw)
        riesgo = calcular_riesgo(toxico, intencion, emocion_raw)
        confianza = max(emocion_pred.probas.values())

        return emocion, toxicidad, ghosting, riesgo, intencion, int(confianza * 100)

    except Exception as e:
        print(f"Error en analizar_texto: {e}")
        return "neutral", "no", 0, "🟢 Bajo", "normal", 50
