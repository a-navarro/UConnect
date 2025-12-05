"""
from API_KEY import GEMINI_KEY

from google import genai

client = genai.Client(api_key=GEMINI_KEY)

texto = input("Que le quieres preguntar a la IA?: ")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents=texto
)
print(response.text)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="UniQuest Backend", version="1.0")

# --- MODELOS DE DATOS (Lo que el Bot te envía) ---
class EstudioInput(BaseModel):
    user_id: str
    minutos: int

class Usuario(BaseModel):
    user_id: str
    nombre: str
    xp: int = 0
    nivel: str = "Novato"

# --- BASE DE DATOS SIMULADA (Mientras tus amigos terminan la SQL) ---
# Esto vive en la memoria RAM. Si apagas el server, se borra.
fake_db = [] 

# --- LÓGICA AUXILIAR (Tu cerebro) ---
def calcular_nivel(xp: int) -> str:
    pass

def encontrar_usuario(user_id: str):
    for user in fake_db:
        if user["user_id"] == user_id:
            return user
    return None

# --- ENDPOINTS (Las puertas de tu API) ---

@app.get("/")
def home():
    return {"mensaje": "¡UniQuest API está viva!"}

@app.post("/registrar_usuario")
def registrar(user_id: str, nombre: str):
    # Verificar si ya existe
    if encontrar_usuario(user_id):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    nuevo_usuario = {"user_id": user_id, "nombre": nombre, "xp": 0, "nivel": "Novato"}
    fake_db.append(nuevo_usuario)
    return {"mensaje": f"Bienvenido {nombre}", "usuario": nuevo_usuario}

@app.post("/registrar_estudio")
def registrar_estudio(datos: EstudioInput):
    # 1. Buscar usuario
    usuario = encontrar_usuario(datos.user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado. Regístralo primero.")
    
    # 2. TU LÓGICA DE GAMIFICACIÓN AQUÍ
    # Regla: 100 XP por cada 60 minutos (aprox 1.6 XP por minuto)
    xp_ganado = int(datos.minutos * 1.6) 
    
    # Bonus: Si estudia más de 2 horas (120 min), bono de 50 XP
    bonus = 0
    if datos.minutos >= 120:
        bonus = 50
    
    total_xp = xp_ganado + bonus
    
    # 3. Actualizar datos
    usuario["xp"] += total_xp
    usuario["nivel"] = calcular_nivel(usuario["xp"])
    
    return {
        "mensaje": "Estudio registrado",
        "xp_ganado": total_xp,
        "nuevo_total": usuario["xp"],
        "nuevo_nivel": usuario["nivel"]
    }

@app.get("/ranking")
def obtener_ranking():
    ranking = sorted(fake_db, key=lambda x: x["xp"], reverse=True)
    return ranking