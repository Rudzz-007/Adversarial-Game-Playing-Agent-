from fastapi import FastAPI

app = FastAPI(
    title="Connect Four AI Agent",
    description="Backend API for the Connect Four adversarial game-playing agent",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Connect Four AI API is running",
        "project": "Adversarial Game-Playing Agent",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
