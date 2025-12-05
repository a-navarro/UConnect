from API_KEY import GEMINI_KEY

from google import genai

client = genai.Client(api_key=GEMINI_KEY)

texto = input("Que le quieres preguntar a la IA?: ")

response = client.models.generate_content(
    model="gemini-2.5-flash", contents=texto
)
print(response.text)
