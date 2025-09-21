from fastapi import FastAPI
from .database import engine, Base
from .api.v1.endpoints import router as api_v1_router
from fastapi.middleware.cors import CORSMiddleware

# This should be the ONLY place this line exists in your project
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Foresight AI")

# Add CORS middleware
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Market Maven API!"}