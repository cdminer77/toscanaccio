from fastapi import FastAPI

app = FastAPI(title="Toscanaccio Test")

@app.get("/")
def home():
    return {"messaggio": "✅ Toscanaccio backend funziona!"}

@app.get("/menu")
def menu():
    return [
        {"id": 1, "nome": "Pappa al Pomodoro", "prezzo": 9.90},
        {"id": 2, "nome": "Cinta Senese Experience", "prezzo": 28.0}
    ]