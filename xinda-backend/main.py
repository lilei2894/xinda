from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import sys
import argparse

from routers import upload, process, history, config, result, providers, prompts
from models.database import SessionLocal, seed_default_providers

load_dotenv()

app = FastAPI(title="xinda API", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(process.router, prefix="/api/process", tags=["process"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(result.router, prefix="/api/result", tags=["result"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
app.include_router(prompts.router, prefix="/api/prompts", tags=["prompts"])

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        seed_default_providers(db)
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "xinda API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    args = parser.parse_args()
    
    uvicorn.run(app, host="0.0.0.0", port=args.port)