import pandas as pd
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os
import uuid # Para generar IDs de log únicos de forma sencilla

# --- CONFIGURACIÓN ---
app = Flask(__name__)
# Rutas relativas a la carpeta 'database'
USUARIOS_CSV = 'database/usuarios.csv'
REGISTROS_XP_CSV = 'database/registros.csv'

# Asegurar que la carpeta 'database' exista al inicio
if not os.path.exists('database'):
    os.makedirs('database')

# --- FUNCIONES DE MANEJO DE DATOS ---

def cargar_dataframes():
    """
    Carga los DataFrames desde los archivos CSV. 
    Implementa lógica robusta para manejar archivos vacíos o inexistentes.
    """
    
    # Definición de DataFrames vacíos con las columnas esperadas
    columnas_usuarios = ['telegram_id', 'nombre', 'xp_total', 'liga_actual', 'fecha_creacion']
    df_u = pd.DataFrame(columns=columnas_usuarios)
    
    columnas_registros = ['log_id', 'telegram_id', 'xp_ganado', 'tipo_actividad', 'fecha_registro']
    df_r = pd.DataFrame(columns=columnas_registros)
    
    # 1. Manejo del DataFrame de Usuarios
    if os.path.exists(USUARIOS_CSV) and os.path.getsize(USUARIOS_CSV) > 0:
        try:
            df_u = pd.read_csv(USUARIOS_CSV)
        except pd.errors.EmptyDataError:
            # Si el archivo tiene encabezado pero no datos, o falló la lectura: 
            # se queda con el DataFrame vacío inicializado
            print(f"Advertencia: El archivo {USUARIOS_CSV} existe pero está vacío o es ilegible. Inicializando un DataFrame vacío.")
            pass # df_u ya está inicializado arriba

    # 2. Manejo del DataFrame de Registros
    if os.path.exists(REGISTROS_XP_CSV) and os.path.getsize(REGISTROS_XP_CSV) > 0:
        try:
            df_r = pd.read_csv(REGISTROS_XP_CSV)
        except pd.errors.EmptyDataError:
            # Si el archivo tiene encabezado pero no datos, o falló la lectura:
            # se queda con el DataFrame vacío inicializado
            print(f"Advertencia: El archivo {REGISTROS_XP_CSV} existe pero está vacío o es ilegible. Inicializando un DataFrame vacío.")
            pass # df_r ya está inicializado arriba
        
    return df_u, df_r

def guardar_dataframes(df_u, df_r):
    """Guarda los DataFrames en los archivos CSV."""
    df_u.to_csv(USUARIOS_CSV, index=False)
    df_r.to_csv(REGISTROS_XP_CSV, index=False)

# --- ENDPOINTS DE LA API ---

@app.route('/', methods=['GET'])
def inicio_api():
    return "Bienvenido a UConnect!"


## 1. POST: Registrar Actividad y Sumar XP
@app.route('/api/registrar_actividad', methods=['POST'])
def registrar_actividad():
    """
    Ruta para que el bot de Telegram envíe un registro de actividad.
    Datos esperados en el cuerpo JSON: telegram_id, tipo_actividad, xp_a_sumar
    """
    data = request.json
    
    # Validación de datos básicos
    if not all(key in data for key in ['telegram_id', 'tipo_actividad', 'xp_a_sumar']):
        return jsonify({"error": "Faltan campos requeridos (telegram_id, tipo_actividad, xp_a_sumar)"}), 400

    try:
        # Intenta convertir a int. Si falla, genera error 400.
        telegram_id = int(data['telegram_id'])
        xp_a_sumar = int(data['xp_a_sumar'])
        tipo_actividad = data['tipo_actividad']
    except ValueError:
        return jsonify({"error": "telegram_id y xp_a_sumar deben ser números enteros."}), 400

    # 1. Cargar DataFrames
    df_usuarios, df_registros = cargar_dataframes()
    
    # Buscar el usuario
    idx = df_usuarios[df_usuarios['telegram_id'] == telegram_id].index
    
    if idx.empty:
        return jsonify({"error": f"Usuario con ID {telegram_id} no encontrado. Debe registrarse primero."}), 404

    # 2. Registrar la actividad (Append a Registros_XP)
    nuevo_log = {
        'log_id': str(uuid.uuid4()), # Usar UUID como log_id único
        'telegram_id': telegram_id,
        'xp_ganado': xp_a_sumar,
        'tipo_actividad': tipo_actividad,
        'fecha_registro': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    # Concatenar el nuevo registro
    df_registros = pd.concat([df_registros, pd.DataFrame([nuevo_log])], ignore_index=True)

    # 3. Actualizar el XP total del usuario (Update en Usuarios)
    # Convertimos a float para asegurar operaciones, aunque luego se devuelva como int
    df_usuarios.loc[idx, 'xp_total'] = df_usuarios.loc[idx, 'xp_total'].astype(float) + xp_a_sumar

    # 4. Guardar los archivos
    guardar_dataframes(df_usuarios, df_registros)

    return jsonify({
        "status": "success",
        "xp_ganado": xp_a_sumar,
        "xp_total_actual": int(df_usuarios.loc[idx, 'xp_total'].iloc[0]) # Devolver el nuevo total
    }), 200

## 2. GET: Obtener Ranking Semanal
@app.route('/api/ranking_semanal', methods=['GET'])
def obtener_ranking_semanal():
    """
    Ruta para obtener el ranking de XP de los últimos 7 días.
    """
    df_usuarios, df_registros = cargar_dataframes()

    if df_registros.empty:
        return jsonify({"ranking": [], "mensaje": "No hay registros de actividad para calcular el ranking."}), 200

    # Convertir a datetime y definir el rango (últimos 7 días)
    # Aseguramos que la columna exista y sea tratable
    if 'fecha_registro' not in df_registros.columns or df_registros['fecha_registro'].dtype == object:
        df_registros['fecha_registro'] = pd.to_datetime(df_registros['fecha_registro'], errors='coerce')
        # Limpiar filas donde la fecha no se pudo parsear
        df_registros.dropna(subset=['fecha_registro'], inplace=True)
    
    hace_siete_dias = datetime.now() - timedelta(days=7)

    # 1. Filtrar solo los registros de la última semana
    df_semanal = df_registros[df_registros['fecha_registro'] > hace_siete_dias]

    # 2. Agrupar por telegram_id y sumar el XP
    ranking_xp = df_semanal.groupby('telegram_id')['xp_ganado'].sum().reset_index()
    ranking_xp.rename(columns={'xp_ganado': 'xp_semanal'}, inplace=True)

    # 3. Ordenar y obtener los Top
    ranking_xp = ranking_xp.sort_values(by='xp_semanal', ascending=False)
    
    # 4. Fusionar con la tabla Usuarios para obtener el nombre
    ranking_final = pd.merge(ranking_xp, df_usuarios[['telegram_id', 'nombre']], on='telegram_id', how='left')
    
    # 5. Convertir a formato JSON para la respuesta
    # Reemplazar NaN por 'Desconocido' si algún ID no tiene nombre
    ranking_final['nombre'].fillna('Usuario Desconocido', inplace=True)
    
    # Seleccionar las columnas relevantes y convertir a lista de diccionarios
    respuesta = ranking_final[['nombre', 'xp_semanal']].head(10).to_dict('records')
    
    return jsonify({"ranking": respuesta}), 200


# 3. POST: Ruta para nuevo registro (si el bot ve un ID nuevo)
@app.route('/api/registrar_usuario', methods=['POST'])
def registrar_usuario():
    """Ruta para añadir un nuevo usuario a la base de datos."""
    data = request.json
    if not all(key in data for key in ['telegram_id', 'nombre']):
        return jsonify({"error": "Faltan campos requeridos (telegram_id, nombre)"}), 400

    try:
        telegram_id = int(data['telegram_id'])
    except ValueError:
        return jsonify({"error": "telegram_id debe ser un número entero."}), 400

    df_usuarios, df_registros = cargar_dataframes()

    # Verificar si ya existe
    if not df_usuarios[df_usuarios['telegram_id'] == telegram_id].empty:
        return jsonify({"error": "El usuario ya está registrado."}), 409

    nuevo_usuario = {
        'telegram_id': telegram_id,
        'nombre': data['nombre'],
        'xp_total': 0,
        'liga_actual': 'Novato',
        'fecha_creacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    df_usuarios = pd.concat([df_usuarios, pd.DataFrame([nuevo_usuario])], ignore_index=True)
    
    # CORRECCIÓN: Guardar ambos dataframes 
    guardar_dataframes(df_usuarios, df_registros) 

    return jsonify({"status": "success", "mensaje": "Usuario registrado correctamente."}), 201


# --- INICIAR LA APLICACIÓN ---
if __name__ == '__main__':
    # Esto asegura que los DataFrames se carguen/inicialicen antes de correr la app
    # Cargar y guardar solo para crear los archivos (con sus cabeceras) si no existen
    guardar_dataframes(*cargar_dataframes())
    
    print("\n--- INICIANDO API DE FLASK ---")
    print("API lista en http://localhost:5000/")
    # Asegúrate de ejecutar este archivo desde la carpeta donde se encuentra
    app.run(debug=True)