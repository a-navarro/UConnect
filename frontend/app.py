from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

API_URL = "http://localhost:5000/api"  # Ajusta si tu API está en otro host


@app.get("/")
def login():
    return render_template("login.html")


@app.post("/login")
def do_login():
    user_input = request.form.get("user_id")
    if not user_input:
        return "Falta el ID", 400
    
    return redirect(url_for("perfil", telegram_id=user_input))


@app.get("/perfil/<telegram_id>")
def perfil(telegram_id):
    resp = requests.get(f"{API_URL}/usuario/{telegram_id}")

    if resp.status_code != 200:
        return f"Usuario {telegram_id} no encontrado", 404

    datos = resp.json()
    return render_template("perfil.html", user=datos)


if __name__ == "__main__":
    app.run(port=3000, debug=True)
