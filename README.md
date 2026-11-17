# 🤖 Chat Analyzer Bot

**Chat Analyzer Bot** es un bot de Telegram que usa Inteligencia Artificial y Procesamiento de Lenguaje Natural (NLP) para analizar mensajes de texto en español. Detecta emociones, toxicidad, intención comunicativa, nivel de ghosting y riesgo de conflicto, y **sugiere cómo responder** a cada mensaje.

---

## 📋 Tabla de contenidos

- [Características](#-características)
- [Agregado: historial y resumen](#-agregado-historial-y-resumen-de-la-conversación)
- [Tecnologías](#️-tecnologías)
- [Instalación](#-instalación)
- [Configuración y ejecución](#️-configuración-y-ejecución)
- [Uso](#-uso)
- [Ejemplos](#-ejemplos)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Posibles mejoras](#-posibles-mejoras)
- [Notas de seguridad](#️-notas-de-seguridad)

---

## ✨ Características

| Característica | Descripción |
|----------------|-------------|
| 🎭 **Análisis emocional** | 7 emociones: positivo, tristeza, enojo, sorpresa, disgusto, miedo, neutral |
| 🚫 **Detección de toxicidad** | Lenguaje ofensivo, agresivo o dañino (modelo `hate_speech` + reglas) |
| 🧠 **Clasificación de intención** | 12 intenciones: afecto, reclamo, celos, agresión, ruptura, manipulación, control, desinterés, inseguridad, curiosidad, tristeza, normal |
| 💔 **Métrica de ghosting** | Probabilidad de desinterés o distanciamiento (0-95%) |
| 🔥 **Evaluación de riesgo** | 🔴 Alto, 🟡 Medio, 🟢 Bajo |
| 🎯 **Confianza del modelo** | Probabilidad de la emoción detectada |
| 💬 **Sugerencias de respuesta** | Te dice **cómo responder** al mensaje que recibiste |
| 🗂️ **Historial y resumen** *(nuevo)* | Guarda tus últimos 20 análisis y muestra la evolución emocional |
| 🧭 **Consejos personalizados** *(nuevo)* | Comando `/consejo` con recomendaciones según la conversación |

---

## 🆕 Agregado: historial y resumen de la conversación

Antes el bot analizaba cada mensaje de forma aislada. Ahora recuerda los últimos 20 mensajes analizados por cada usuario (en memoria) y permite ver la conversación completa:

| Comando | Qué hace |
|---------|----------|
| `/start` | Mensaje de bienvenida con la lista de comandos |
| `/ayuda` | Muestra la ayuda |
| `/historial` | Lista los últimos mensajes analizados con su emoción, intención y riesgo |
| `/resumen` | Porcentaje de cada emoción, intenciones más frecuentes, mensajes tóxicos y de riesgo alto, ghosting promedio y **tendencia** (si la conversación se enfría o se calienta) |
| `/consejo` | **(función nueva)** Da un consejo personalizado según cómo va la conversación |
| `/consejo <mensaje>` | Da un consejo para un mensaje concreto, ej: `/consejo con quién estabas` |
| `/borrar` | Borra tu historial |

Si en el resumen se repiten señales de agresión, control o manipulación, el bot muestra un aviso sugiriendo hablar con alguien de confianza.

**Mejoras al motor de análisis (`predict.py`):**

- Se ignoran las tildes: "por que no respondes" y "por qué no respondes" se detectan igual.
- Se buscan palabras completas: "ya" ya no coincide con "playa", ni "ah" con "ahora".
- "me siento mal" ahora es *tristeza* (antes caía en *agresión* por la palabra "mal").
- "qué haces" ahora es *curiosidad* (antes era *control*).
- Se agregó la intención *inseguridad* ("¿todavía me quieres?"), que estaba documentada pero no se detectaba.
- Toxicidad corregida: el modelo `hate_speech` de pysentimiento devuelve una **lista** de etiquetas y el código anterior la comparaba con un texto, así que nunca marcaba toxicidad.

### 🧭 Función nueva: `/consejo`

Revisa los mensajes analizados y elige el consejo más importante:

1. Si aparece algo grave (agresión, control, manipulación o ruptura), el consejo se centra en eso aunque no sea lo más frecuente.
2. Si no, se basa en la intención que más se repite (afecto, desinterés, celos…).
3. Añade avisos extra si hubo mensajes tóxicos o si el ghosting promedio supera el 50 %.
4. Con 4 o más mensajes, indica si la conversación se enfría o se calienta.

Ejemplo de respuesta:

```
🧭 Consejo según tus últimos 5 mensaje(s)
━━━━━━━━━━━━━━━━━━━━
🛑 Hay agresividad en la conversación. No respondas en caliente: pon un
límite claro y retoma cuando ambos estén calmados. Nadie merece insultos.

🚩 1 mensaje(s) fueron tóxicos. Protege tu bienestar: no tienes que
tolerar faltas de respeto.
```

---

## 🛠️ Tecnologías

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| Python | 3.11 | Lenguaje principal |
| pysentimiento | 0.7.3 | NLP para español (emociones y hate speech) |
| Transformers | 4.44.2 | Modelos BERT |
| PyTorch | 2.2+ (CPU) | Deep learning |
| NumPy | < 2.0 | Compatibilidad en Windows (2.x falla con error de DLL en algunos equipos) |
| python-telegram-bot | 20.7 | Framework del bot |

---

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/rubisabel00/machine-learning-Bot-telegram.git
cd machine-learning-Bot-telegram
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

---

## ⚙️ Configuración y ejecución

### 1. Crear tu propio bot en Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Elige un nombre (ej: `Chat Analyzer Bot`)
4. Elige un username terminado en `bot` (ej: `mi_chat_analyzer_bot`)
5. Copia el token que te entrega BotFather

### 2. Configurar el token

```powershell
# Windows (PowerShell)
$env:TELEGRAM_TOKEN="tu_token_aqui"
```

```bat
:: Windows (CMD)
set TELEGRAM_TOKEN=tu_token_aqui
```

```bash
# Linux / Mac
export TELEGRAM_TOKEN="tu_token_aqui"
```

### 3. Ejecutar

```bash
python bot.py
```

Salida esperada (la primera vez descarga los modelos, puede tardar unos minutos):

```
🔄 Cargando modelos de pysentimiento...
✅ Modelos cargados correctamente
🤖 Bot de análisis de mensajes activo...
📌 Analizo los mensajes que TE ENVÍAN y te digo cómo responder
🟢 Bot corriendo... Esperando mensajes
```

---

## 🎯 Uso

1. Busca tu bot en Telegram por su username y pulsa **Iniciar** (`/start`)
2. Escribe o reenvía un mensaje que te hayan enviado
3. El bot responde con el análisis y una sugerencia de respuesta
4. Después de varios mensajes, usa `/historial`, `/resumen` y `/consejo`

---

## 📝 Ejemplos

| Mensaje que te envían | Intención | Riesgo | Sugerencia |
|-----------------------|-----------|--------|------------|
| "te quiero mucho" | Afecto | 🟢 Bajo | "Yo también te quiero mucho ❤️" |
| "por qué no me respondes" | Reclamo | 🟡 Medio | "Entiendo que te sientes ignorado, no fue mi intención" |
| "con quién estabas" | Celos | 🟡 Medio | "No hay nadie más, pero entiendo tu inseguridad" |
| "eres un idiota" | Agresión | 🔴 Alto | "Esto se está poniendo feo, hablemos más tarde" |
| "dónde estás? envía ubicación" | Control | 🔴 Alto | "Confío en ti y espero que tú confíes en mí" |
| "ok" | Desinterés | 🟢 Bajo | "¿Estás bien? Parece que no tienes ganas de hablar" |
| "cómo estás" | Curiosidad | 🟢 Bajo | "Todo bien, ¿y tú? Cuéntame" |
| "quiero terminar" | Ruptura | 🟡 Medio | "Hablemos esto en persona, es importante" |
| "¿todavía me quieres?" | Inseguridad | 🟢 Bajo | "Estoy contigo, no tienes nada que temer" |

### Respuesta del bot a un mensaje

```
💕 Análisis del mensaje que te enviaron
━━━━━━━━━━━━━━━━━━━━━━━━━━
😊 Emoción detectada: Positivo
🚩 Toxicidad: 🟢 Baja
🧠 Intención: Afecto
💔 Ghosting: ░░░░░░░░░░ 0%
🔥 Riesgo: 🟢 Bajo
🎯 Confianza del modelo: 91%
━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 Qué significa:
💕 Está expresando cariño y buenos sentimientos.

💬 Cómo responder:
🌸 Corresponde: 'Yo también te quiero mucho ❤️'
```

### Respuesta a `/resumen`

```
📊 Resumen de 9 mensaje(s)
━━━━━━━━━━━━━━━━━━━━
Emociones
😐 Neutral   █████░░░░░ 56%
😊 Positivo  ██░░░░░░░░ 22%
😠 Enojo     ██░░░░░░░░ 22%

Intenciones más frecuentes
⚠️ Agresion: 2
💕 Afecto: 1
😔 Reclamo: 1

🚩 Mensajes tóxicos: 2
🔴 Mensajes de riesgo alto: 2
💔 Ghosting promedio: █░░░░░░░░░ 14%

📉 La conversación se está enfriando: aumentan las señales de distancia.
```

---

## 📁 Estructura del proyecto

```
machine-learning-Bot-telegram/
├── bot.py             # Bot de Telegram: mensajes, comandos e historial
├── predict.py         # Motor de análisis (pysentimiento + reglas)
├── requirements.txt   # Dependencias
├── Indicaciones.txt   # Pasos rápidos de instalación en Windows
└── README.md          # Documentación
```

---

## 🔮 Posibles mejoras

- [x] Historial de conversaciones y evolución emocional
- [ ] Guardar el historial en una base de datos (hoy se pierde al reiniciar)
- [ ] Modelo de intención entrenado con un dataset propio en vez de reglas
- [ ] Análisis de audios (voz a texto)
- [ ] Dashboard web con estadísticas
- [ ] Dockerización para desplegar en la nube

---

## ⚠️ Notas de seguridad

- Nunca compartas tu token de Telegram ni lo subas a GitHub (tampoco en archivos `.txt`).
- Usa variables de entorno para la información sensible.
- Si tu token se expone, revócalo de inmediato: @BotFather → `/mybots` → tu bot → **API Token** → **Revoke current token**.

---

## 🙏 Agradecimientos

- [pysentimiento](https://github.com/pysentimiento/pysentimiento): NLP para español
- [python-telegram-bot](https://python-telegram-bot.org/): framework del bot
- [Hugging Face](https://huggingface.co/): modelos preentrenados

## 📄 Licencia

MIT
