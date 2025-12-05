import logging
import os 
from parametros import API_URL, TOKEN_TELEGRAM
import requests # Necesario para las llamadas a la API de tu backend
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
) 

# --- CONFIGURACIÓN GLOBAL ---
# URL de ejemplo. DEBES cambiarla por la URL real de tu backend
 

# Configuración de Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__) 

# --- 1. FUNCIONES DE CONEXIÓN AL BACKEND (API) ---

def _registrar_usuario_api(user_id, nombre): #aAaAAaAaa 
    """Intenta registrar al usuario en la BD del backend."""
    try:
        response = requests.post(f"{API_URL}/registrar_usuario", json={
            "telegram_id": user_id,
            "nombre": nombre
        })
        response.raise_for_status() # Lanza un error para códigos 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error conectando API al registrar usuario: {e}")
        return None

def _registrar_actividad_api(user_id, tipo, xp):
    """Envía puntos a la API para una actividad."""
    try:
        response = requests.post(f"{API_URL}/registrar_actividad", json={
            "telegram_id": user_id,
            "tipo_actividad": tipo,
            "xp_a_sumar": xp
        })
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        logger.error(f"Error conectando API al registrar actividad: {e}")
        return {"success": False}

def _obtener_perfil_api(user_id):
    """Obtiene datos reales del usuario (XP, ligas, insignias)."""
    try:
        response = requests.get(f"{API_URL}/usuario/{user_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error conectando API al obtener perfil: {e}")
        
        # Datos de simulación en caso de fallo (para que el bot no se caiga)
        return { 
            "xp_total": 0,
            "liga_actual": "No Registrado",
            "insignias": ["Sin Datos"]
        }

def _obtener_ranking_api():
    """Obtiene el Top 10."""
    try:
        response = requests.get(f"{API_URL}/ranking_semanal")
        response.raise_for_status()
        return response.json().get('ranking', [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error conectando API al obtener ranking: {e}")
        return []

# --- 2. HANDLERS DE COMANDOS (CommandHandler) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /start. Da la bienvenida e inicializa el usuario."""
    user = update.effective_user
    _registrar_usuario_api(user.id, user.first_name)
    await update.message.reply_html(
        f"¡Hola {user.first_name}! 👋\n"
        "Bienvenido a **UConnect**.\n"
        "Comienza a ganar XP registrando tu `/estudio` y `/asistencia`.\n"
        "Usa `/miperfil` para ver tu progreso."
    )

async def miperfil_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el XP, liga e insignias del usuario."""
    user_id = update.effective_user.id 
    datos = _obtener_perfil_api(user_id) # Usa la función real de API

    if not datos:
        await update.message.reply_text("⚠️ No te encontré en la base de datos. Usa /start primero.")
        return
    
    perfil_msg = (
        f"👤 **PERFIL DE {update.effective_user.first_name.upper()}**\n\n"
        f"✨ **XP Total:** {datos.get('xp_total', 0)}\n"
        f"🏆 **Liga Actual:** {datos.get('liga_actual', 'No disponible')}\n"
        f"🏅 **Insignias Obtenidas:** {', '.join(datos.get('insignias', ['Ninguna']))}\n\n"
        "¡Sigue sumando XP para subir en el ranking!"
    )
    await update.message.reply_text(perfil_msg, parse_mode="Markdown")

async def ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el top 10 semanal."""
    ranking_data = _obtener_ranking_api()
    
    if not ranking_data:
        ranking_msg = "📊 **RANKING SEMANAL**\n\nNo se pudo obtener el ranking. Intenta más tarde."
    else:
        # Formatear el ranking_data (asumimos que es una lista de objetos con 'nombre' y 'xp')
        ranking_list = [
            f"{i+1}. {p['nombre']} - {p['xp']} XP" + (" 👑" if i == 0 else "")
            for i, p in enumerate(ranking_data[:10])
        ]
        
        ranking_msg = (
            "📊 **RANKING SEMANAL DE LA UNIVERSIDAD**\n\n"
            f"{'\n'.join(ranking_list)}\n\n"
            "¡Sigue sumando XP para subir!"
        )
    await update.message.reply_text(ranking_msg, parse_mode="Markdown")

# La función _registrar_estudio_db ahora es una utilidad interna
async def _registrar_estudio_db(user_id, minutos, update, is_command=False):
    """Lógica que registra la actividad de estudio en el backend."""
    
    # Suponemos un XP fijo o calculado aquí antes de enviar
    xp_ganado = minutos * 2 
    
    resultado = _registrar_actividad_api(user_id, "estudio", xp_ganado)
    
    if resultado["success"]:
        mensaje = f"🎉 ¡Bloque de {minutos} minutos registrado! **+{xp_ganado} XP** ganado."
    else:
        mensaje = "❌ Error al registrar el estudio en el backend. ¿Está la API funcionando?"
    
    if is_command:
        # Si viene del /estudio <minutos>
        await update.message.reply_text(mensaje, parse_mode="Markdown")
    else:
        # Si viene del botón
        await update.callback_query.edit_message_text(mensaje, parse_mode="Markdown")


async def estudio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /estudio (INTERACTIVO). Muestra botones para registrar bloques."""
    keyboard = [
        [
            InlineKeyboardButton("20 min (Repaso) 🤓", callback_data="estudio_20"),
            InlineKeyboardButton("45 min (Pomodoro) 🧠", callback_data="estudio_45"),
        ],
        [
            InlineKeyboardButton("60 min (Bloque) 📚", callback_data="estudio_60"),
            InlineKeyboardButton("Otra Cantidad...", callback_data="estudio_otro"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Si viene con argumentos, intenta registrar directamente
    if context.args:
        try:
            minutos = int(context.args[0])
            await _registrar_estudio_db(update.effective_user.id, minutos, update, is_command=True)
        except ValueError: 
            await update.message.reply_text("Formato inválido. Usa /estudio <minutos> o toca un botón.")
        return # Sale de la función si ya procesó argumentos
        
    await update.message.reply_text(
        '¡Elige un bloque de tiempo de estudio o escribe /estudio <minutos>!',
        reply_markup=reply_markup
    )
    

async def asistencia_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Instrucciones para registrar asistencia con QR."""
    asistencia_msg = (
        "📸 **REGISTRO DE ASISTENCIA**\n\n"
        "1. Tomale una foto a tu clase.\n"
        "2. Usa la opción 'Adjuntar' en Telegram y envía tu foto.\n"
        "3. Gemini AI revisará tu foto para ver si es una clase, y revisará los metadatos para ver si la foto es auténtica."
        "4. Tu asistencia quedará registrada con la hora de la foto y se sumarán los puntos a tu perfil!"
    )
    await update.message.reply_text(asistencia_msg, parse_mode="Markdown")

async def sueno_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Registra horas de sueño (requiere argumento)."""
    if not context.args:
        await update.message.reply_text(
            "Por favor, indica las horas de sueño. \n"
            "Usa el formato: `/sueno <horas>` (ej: `/sueno 7.5`)"
        )
        return
    
    try:
        horas = float(context.args[0])
        xp_ganado = 0
        
        if 2 <= horas <= 30: # Rango de horas razonable
            if 7 <= horas <= 9: 
                xp_ganado = 150 # XP extra por sueño adecuado
                mensaje_extra = "¡Felicidades! por un descanso óptimo."
            elif 2 <= horas <= 4:
                xp_ganado = 10
                mensaje_extra = "Gracias por registrarlo. OJO! Recuerda que un descanso óptimo está entre 7 y 9 horas."

            elif 10 <= horas <= 20:
                xp_ganado = 10
                mensaje_extra = "Gracias por registrarlo. OJO! Recuerda que un descanso óptimo está entre 7 y 9 horas."

            resultado = _registrar_actividad_api(update.effective_user.id, "sueno", xp_ganado)
            
            if resultado["success"]: 
                await update.message.reply_text(f"✅ Has registrado {horas} horas de sueño. {mensaje_extra} **+{xp_ganado} XP**.", parse_mode="Markdown")
            else:
                 await update.message.reply_text(f"❌ Error al registrar en el backend. {mensaje_extra}")

        else:
             await update.message.reply_text("Por favor, El rango ")

    except ValueError:
        await update.message.reply_text("Formato inválido. Por favor, usa un número.")

async def misiones_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra las misiones y desafíos activos."""
    misiones_msg = (
        "🎯 **MISIONES ACTIVAS**\n\n"
        "**Diarias:**\n"
        "• **Concentración:** Registra 2 bloques de estudio de 45 min. (Recompensa: +300 XP)\n\n"
        "**Semanales:**\n"
        "• **Perfect Attendance:** Asiste a 5 clases distintas. (Recompensa: +1000 XP y un pin virtual)"
    )
    await update.message.reply_text(misiones_msg, parse_mode="Markdown")

# --- 3. HANDLER DE BOTONES (CallbackQueryHandler) ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja las interacciones de los botones en línea (Inline Keyboards)."""
    query = update.callback_query
    await query.answer() # Obligatorio para cerrar la animación de "cargando"

    data = query.data
    user_id = query.from_user.id

    if data.startswith("estudio_"):
        
        if data == "estudio_otro":
            # Si el usuario eligió "Otra Cantidad...", pedimos los minutos
            await query.edit_message_text("Por favor, dime cuántos minutos estudiaste. En formato /estudio [número]")
            # Nota: Para manejar esta respuesta, en un proyecto más complejo se usaría un ConversationHandler.
        
        else:
            # Botones predefinidos (estudio_20, estudio_45, estudio_60)
            minutos = int(data.split('_')[1])
            await _registrar_estudio_db(user_id, minutos, update)

# --- 4. HANDLER DE MENSAJES DE TEXTO LIBRE (IA - Gemini) ---

async def ia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja cualquier texto que no sea un comando y lo trata como consulta IA."""
    texto_usuario = update.message.text
    
    # OBTENER LA CLAVE DE GEMINI DESDE LAS VARIABLES DE ENTORNO
    GEMINI_KEY = os.getenv("GEMINI_API_KEY") 
    
    if not GEMINI_KEY:
        logger.error("La clave de Gemini (GEMINI_API_KEY) no está configurada en las variables de entorno.")
        await update.message.reply_text("❌ Error IA: La clave del modelo Gemini no está configurada. Pide ayuda al administrador.")
        return
        
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_KEY)

        # Muestra un mensaje de espera
        await update.message.reply_text("💭 Procesando tu consulta con IA...")

        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=texto_usuario,
            # Se puede añadir un System Instruction aquí si el bot debe actuar como tutor
        )
        
        await update.message.reply_text(response.text) # Telegram puede manejar Markdown automáticamente

    except ImportError:
        logger.critical("El paquete 'google-genai' no está instalado. Ejecuta 'pip install google-genai'.")
        await update.message.reply_text("❌ Error IA: Falta la librería de Gemini. Contacta al administrador.")
    except Exception as e:
        logger.error(f"Error en el handler de IA: {e}")
        await update.message.reply_text("❌ Error IA: Ocurrió un problema al conectar con el modelo de lenguaje.")

# --- 5. FUNCIÓN PRINCIPAL (MAIN) ---

def main() -> None:
    """Inicia el bot."""
    
    if not TOKEN_TELEGRAM:
        logger.critical("Bot no iniciado. Falta el TOKEN de Telegram.")
        return 
        
    logger.info("Iniciando Bot UConnect...")
    
    # 1. Crea la aplicación y pásale el token
    application = Application.builder().token(TOKEN_TELEGRAM).build()

    # 2. Asigna los Handlers (Manejadores de Comandos y Mensajes)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("miperfil", miperfil_command))
    application.add_handler(CommandHandler("ranking", ranking_command))
    application.add_handler(CommandHandler("estudio", estudio_command))
    application.add_handler(CommandHandler("asistencia", asistencia_command))
    application.add_handler(CommandHandler("sueno", sueno_command))
    application.add_handler(CommandHandler("misiones", misiones_command))
    
    # Handler para los botones interactivos
    application.add_handler(CallbackQueryHandler(button_handler))

    # Handler para el IA: Responde a cualquier texto que NO sea un comando
    # Asegúrate de que este sea el ÚLTIMO MessageHandler añadido
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ia_handler))

    # 3. Inicia el bot 
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 