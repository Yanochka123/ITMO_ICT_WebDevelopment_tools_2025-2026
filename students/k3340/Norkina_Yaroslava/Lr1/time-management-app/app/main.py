# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
import os

from app.database import init_db
from app.routes_loader import load_routes

app = FastAPI(
    title="Time Management App",
    description="API для управления задачами и временем",
    version="2.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Загрузка маршрутов
routes = load_routes()
app.include_router(routes["auth"].router)
app.include_router(routes["tasks"].router)
app.include_router(routes["time_entries"].router)
app.include_router(routes["analytics"].router)
app.include_router(routes["categories"].router)
app.include_router(routes["tags"].router)
app.include_router(routes["schedules"].router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Time Management API is running"}