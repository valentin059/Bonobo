from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, peliculas, acciones, usuarios

app = FastAPI(title="Bonobo API")

origins = ["*"]  #En producción cambiaremos esto por la URL del frontend

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(peliculas.router)
app.include_router(acciones.router)
app.include_router(usuarios.router)

@app.get("/")
def root():
    return {"message": "Bonobo API funcionando"}