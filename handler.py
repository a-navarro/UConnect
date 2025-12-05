# handlers.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import logging

logger = logging.getLogger(__name__)

# --- FUNCIONES PLACEHOLDER (DEBES CONECTAR A TU BACKEND/DB AQUÍ) ---
# Simulación de la función de registro de XP (necesaria para el ejemplo)
def registrar_xp(user_id, xp, activity_type):
    logger.info(f"DB Log: User {user_id} registered {xp} XP for {activity_type}")
    return True

def obtener_ranking(periodo):
    """Simula la obtención de datos del ranking por periodo."""
    if periodo == 'semanal':
        return ["1. Ana R. - 12,500 XP 👑", "2. Ben S. - 11,900 XP"]
    elif periodo == 'mensual':
        return ["1. Zaira T. - 45,000 XP 🏆", "2. Max P. - 40,500 XP"]
    elif periodo == 'semestral':
        return ["1. El Fundador - 100,000 XP ⭐", "2. El Mentor - 98,000 XP"]
    return []

# --- HANDLERS DE COMANDOS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja /start."""
    user = update.effective_user
    await update.message.reply_html(
        f"¡Hola {user.first_name}! 👋\n"
        "Bienvenido/a a **UConnect**. Empieza a ganar XP para subir en el `/ranking`."
    )

async def miperfil_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra el XP, liga e insignias."""
    # Lógica: Llama a la DB para obtener los datos del usuario.
    await update.message.reply_text("👤 Perfil: [Conectando a la DB...]", parse_mode="Markdown")


# 🚨 COMANDO DE RANKING ACTUALIZADO PARA SER INTERACTIVO 🚨
async def ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra un menú para elegir el periodo del ranking."""
    keyboard = [
        [
            InlineKeyboardButton("🥇 Semanal", callback_data="ranking_semanal"),
            InlineKeyboardButton("🥈 Mensual", callback_data="ranking_mensual"),
            InlineKeyboardButton("🥉 Semestral", callback_data="ranking_semestral"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '📊 ¿Qué periodo del **Ranking UConnect** quieres consultar?',
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def estudio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /estudio (INTERACTIVO). Muestra botones."""
    keyboard = [
        [
            InlineKeyboardButton("20 min 🤓", callback_data="estudio_20"),
            InlineKeyboardButton("45 min 🧠", callback_data="estudio_45"),
        ],
        [
            InlineKeyboardButton("60 min 📚", callback_data="estudio_60"),
            InlineKeyboardButton("Otra Cantidad...", callback_data="estudio_otro"), #OJO ATENCIÓN ATENTOS
        ] 
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        '¡A estudiar! Elige un bloque de tiempo de estudio:',
        reply_markup=reply_markup
    )

# ... (Otros comandos como /sueno, /asistencia, /misiones) ...


# --- HANDLER DE BOTONES (CallbackQueryHandler) ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja las interacciones de los botones en línea."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    
    # ----------------------------------------------
    # 1. Lógica para el RANKING (Nuevo)
    # ----------------------------------------------
    if data.startswith("ranking_"):
        periodo = data.split('_')[1] # Obtiene 'semanal', 'mensual' o 'semestral'
        ranking_data = obtener_ranking(periodo)
        
        periodo_str = periodo.upper()
        ranking_msg = f"🏆 **RANKING {periodo_str} DE UCONNECT**\n\n"
        
        if ranking_data:
            ranking_msg += '\n'.join(ranking_data)
        else:
            ranking_msg += "No hay datos de ranking para este periodo todavía."
            
        await query.edit_message_text(ranking_msg, parse_mode="Markdown")

    # ----------------------------------------------
    # 2. Lógica para ESTUDIO (Existente)
    # ----------------------------------------------
    elif data.startswith("estudio_"):
        if data == "estudio_otro":
            await query.edit_message_text("Por favor, dime cuántos minutos estudiaste.")
        else:
            minutos = int(data.split('_')[1])
            xp_ganado = minutos * 2 # Cálculo simple
            
            if registrar_xp(user_id, xp_ganado, 'Estudio'):
                await query.edit_message_text(f"🎉 ¡Bloque de {minutos} minutos registrado! **+{xp_ganado} XP**.", parse_mode="Markdown")
            else:
                 await query.edit_message_text("❌ Error al registrar el XP.", parse_mode="Markdown")
    # ... (Más lógica de botones si añades /sueno interactivo, etc.) ...

# --- HANDLER DE IA (Texto Libre) ---
async def ia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja texto libre para consultas a la IA (Gemini)."""
    # Lógica: Llama a la API de Gemini con el texto del usuario.
    respuesta_ia = "Respuesta de la IA simulada."
    await update.message.reply_text(respuesta_ia)

#DEF AYUDA 
async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Muestra un mensaje de apoyo con un botón de enlace directo."""
    
    # 1. Crea el botón de enlace directo (URL Button)
    # Los botones de enlace NO usan callback_data, usan url=
    keyboard = [
        [
            # Reemplaza 'URL_PAGINA_OFICIAL_UC' con el enlace real de apoyo de tu universidad
            InlineKeyboardButton("🏥 Ir a Recursos de Ayuda Mental UC", url="URL_PAGINA_OFICIAL_UC")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # 2. Envía el mensaje y el botón
    await update.message.reply_text(
        "🧠 **RECURSOS DE APOYO UCONNECT**\n\n"
        "Si necesitas ayuda o apoyo profesional, no estás solo/a. Toca el botón de abajo para acceder directamente a los servicios de salud mental y bienestar de la universidad.\n\n"
        "Toma un descanso cuando lo necesites. ¡Tu bienestar es lo primero!", 
        reply_markup=reply_markup,
        parse_mode="Markdown"
    ) 