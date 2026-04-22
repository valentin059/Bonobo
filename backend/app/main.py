from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, peliculas, acciones, usuarios, social, diario, listas
from .routers import logros
# Creamos la aplicación FastAPI. El título aparece en la documentación automática (/docs)
app = FastAPI(title="Bonobo API")

# Lista de orígenes que pueden hacer peticiones a la API.
# "*" significa que cualquier dominio puede acceder (útil en desarrollo).
# En producción hay que poner solo la URL del frontend.
origins = ["*"]

# Configuramos CORS (Cross-Origin Resource Sharing).
# Sin esto, el navegador bloquea las peticiones del frontend hacia la API
# porque están en dominios/puertos distintos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # quién puede llamar a la API
    allow_credentials=True,      # permite enviar cookies/tokens
    allow_methods=["*"],         # permite todos los métodos HTTP (GET, POST, PUT, DELETE...)
    allow_headers=["*"],         # permite todas las cabeceras
)

# Registramos todos los routers (grupos de rutas).
# Cada router está en su propio archivo dentro de /routers/.
app.include_router(auth.router)            # rutas de registro y login
app.include_router(peliculas.router)       # rutas para buscar y ver películas
app.include_router(acciones.router)        # rutas para marcar vistas, watchlist, me gusta...
app.include_router(usuarios.router)        # rutas de perfil y datos de usuarios
app.include_router(social.router)          # rutas para seguir/dejar de seguir usuarios
app.include_router(diario.router_diario)   # rutas del diario (entradas, likes, comentarios)
app.include_router(diario.router_comentarios)  # rutas para eliminar comentarios
app.include_router(listas.router)          # rutas para gestionar listas de películas
app.include_router(logros.router)          # 👈 aquí, después de crear app

# Ruta raíz para comprobar que la API está funcionando
@app.get("/")
def root():
    return {"message": "Bonobo API funcionando"}