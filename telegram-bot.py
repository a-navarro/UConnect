import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = "8250438025:AAFA2IUTLhseiPwo_6wWTJ-lkHqf54pcBKA" 
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- FUNCIONES PLACEHOLDER (DEBES CONECTAR A TU BACKEND/DB AQUÍ) ---

def _conectar_a_backend(endpoint, datos):
    """
    Función placeholder para simular la conexión con tu API/DB.
    """
    # Ejemplo: requests.post(f"https://tu_api.com/{endpoint}", json=datos)
    logger.info(f"Simulando llamada a API: {endpoint} con datos: {datos}")
    
    if endpoint == "registrar_estudio":
        xp_ganado = len(datos.get('minutos', 0)) * 2 # XP simple por minuto
        return {"success": True, "xp": xp_ganado}
    
    return {"success": True, "message": "Operación simulada con éxito."}

def _obtener_datos_perfil(user_id):
    # Simula la obtención de datos del perfil
    return { #ACÁ ACTUALIZAR LOS RANGOS DE APRENDIZ, MADRUGADOR ETC...
        "xp_total": 4500,
        "liga_actual": "Aprendiz (Plata)",
        "insignias": ["Madrugador", "Guerrero Semanal"]
    }

# --- 2. HANDLERS DE COMANDOS (CommandHandler) ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /start. Da la bienvenida e inicializa el usuario."""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola {user.first_name}! 👋\n"
        "Bienvenido a **UConnect**.\n" #welcome to facebook 
        "Comienza a ganar XP registrando tu `/estudio` y `/asistencia`.\n"
        "Usa `/miperfil` para ver tu progreso."
    )

async def miperfil_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el XP, liga e insignias del usuario."""
    user_id = update.effective_user.id 
    datos = _obtener_datos_perfil(user_id)
    
    perfil_msg = (
        f"👤 **PERFIL DE {update.effective_user.first_name.upper()}**\n\n"
        f"✨ **XP Total:** {datos['xp_total']}\n"
        f"🏆 **Liga Actual:** {datos['liga_actual']}\n"
        f"🏅 **Insignias Obtenidas:** {', '.join(datos['insignias'])}\n\n"
        "¡Sigue sumando XP para subir en el ranking!"
    )
    await update.message.reply_text(perfil_msg, parse_mode="Markdown")

async def ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el top 10 semanal."""
    # Aquí puedes añadir el menú de botones (Semanal/Mensual) si quieres más interactividad.
    # Simulación del ranking (debería venir de tu backend)
    ranking_list = [
        "1. Ana R. - 12,500 XP 👑",
        "2. Ben S. - 11,900 XP",
        "3. Cris M. - 10,200 XP",
        "...",
    ]
    ranking_msg = (
        "📊 **RANKING SEMANAL DE LA UNIVERSIDAD**\n\n"
        f"{'\n'.join(ranking_list)}\n\n"
        f"Tu posición actual: #25"
    )
    await update.message.reply_text(ranking_msg, parse_mode="Markdown")

async def estudio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Comando /estudio (INTERACTIVO). Muestra botones para registrar bloques.
    La lógica real se maneja en button_handler.
    """
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
    await update.message.reply_text(
        '¡Elige un bloque de tiempo de estudio o escribe /estudio <minutos>!',
        reply_markup=reply_markup
    )
    
    # Permite el uso de argumentos si el usuario lo prefiere (ej: /estudio 120)
    if context.args:
        try:
            minutos = int(context.args[0])
            await _registrar_estudio_db(update.effective_user.id, minutos, update, is_command=True)
        except ValueError:
            await update.message.reply_text("Formato inválido. Usa /estudio <minutos> o toca un botón.")

async def asistencia_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Instrucciones para registrar asistencia con QR."""
    asistencia_msg = (
        "📸 **REGISTRO DE ASISTENCIA (QR)**\n\n"
        "1. Pide al profesor que muestre el Código QR en clase.\n"
        "2. Usa la opción 'Adjuntar' (el clip) en Telegram y luego 'Escanear QR' para enviármelo.\n"
        "3. Recibirás tu XP de asistencia y puntualidad (si es dentro de los primeros 10 minutos)."
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
        if 5 <= horas <= 12: # Rango de horas razonable
            resultado = _conectar_a_backend("registrar_sueno", {"user_id": update.effective_user.id, "horas": horas})
            
            if 7 <= horas <= 9:
                xp_ganado = 150 # XP extra por sueño adecuado
                await update.message.reply_text(f"✅ Has registrado {horas} horas de sueño. ¡Felicidades! **+150 XP** por un descanso óptimo.", parse_mode="Markdown")
            else:
                xp_ganado = 50
                await update.message.reply_text(f"✅ Has registrado {horas} horas de sueño. **+50 XP**.", parse_mode="Markdown")
        else:
             await update.message.reply_text("Por favor, ingresa un valor de horas de sueño razonable (entre 5 y 12).")

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

async def _registrar_estudio_db(user_id, minutos, update, is_command=False):
    """Lógica que registra la actividad de estudio en el backend."""
    
    resultado = _conectar_a_backend("registrar_estudio", {"user_id": user_id, "minutos": minutos})
    
    if resultado["success"]:
        xp_ganado = resultado.get("xp", minutos * 2)
        mensaje = f"🎉 ¡Bloque de {minutos} minutos registrado! **+{xp_ganado} XP** ganado."
    else:
        mensaje = "❌ Error al registrar el estudio. Inténtalo de nuevo."
    
    if is_command:
        # Si viene del /estudio <minutos>
        await update.message.reply_text(mensaje, parse_mode="Markdown")
    else:
        # Si viene del botón
        await update.callback_query.edit_message_text(mensaje, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja las interacciones de los botones en línea (Inline Keyboards)."""
    query = update.callback_query
    await query.answer()  # Obligatorio para cerrar la animación de "cargando"

    data = query.data
    user_id = query.from_user.id

    if data.startswith("estudio_"):
        
        if data == "estudio_otro":
            # Si el usuario eligió "Otra Cantidad...", pedimos los minutos
            await query.edit_message_text("Por favor, dime cuántos minutos estudiaste.")
            # Nota: Para manejar esta respuesta, en un proyecto más complejo se usaría un ConversationHandler.
        
        else:
            # Botones predefinidos (estudio_20, estudio_45, estudio_60)
            minutos = int(data.split('_')[1])
            await _registrar_estudio_db(user_id, minutos, update)

# --- 4. HANDLER DE MENSAJES DE TEXTO LIBRE (IA - Gemini) ---

async def ia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja cualquier texto que no sea un comando y lo trata como consulta IA."""
    texto_usuario = update.message.text
    
    # 1. Simula el procesamiento de la consulta (Aquí conectarías a la API de Gemini)
    await update.message.reply_text("🤔 *Pensando... (Simulando consulta a la IA Gemini)...*", parse_mode="Markdown")
    
    # 2. Respuesta simulada
    respuesta_ia = (
        f"**Pregunta:** *{texto_usuario}*\n\n"
        "**Respuesta de Gemini (Simulada):** Para tu hackathon, "
        "te sugiero investigar la diferencia entre Flask y FastAPI en el manejo de peticiones asíncronas."
    )
    
    await update.message.reply_text(respuesta_ia, parse_mode="Markdown")


# --- 5. FUNCIÓN PRINCIPAL (MAIN) ---

def main() -> None:
    """Inicia el bot."""
    
    logger.info("Iniciando Bot University Quest...")
    
    # 1. Crea la aplicación y pásale el token
    application = Application.builder().token(TOKEN).build()

    # 2. Asigna los Handlers (Manejadores de Comandos y Mensajes)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("miperfil", miperfil_command))
    application.add_handler(CommandHandler("ranking", ranking_command))
    application.add_handler(CommandHandler("estudio", estudio_command))
    application.add_handler(CommandHandler("asistencia", asistencia_command))
    application.add_handler(CommandHandler("sueno", sueno_command))
    application.add_handler(CommandHandler("misiones", misiones_command))
    
    # Handler para los botones interactivos (ej. los del /estudio)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Handler para el IA: Responde a cualquier texto que NO sea un comando
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ia_handler))

    # 3. Inicia el bot (polling significa que revisa Telegram cada cierto tiempo)
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Asegúrate de haber reemplazado 'TU_BOT_TOKEN' en la línea 17
    main()