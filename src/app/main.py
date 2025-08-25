from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello from python-starter-template!"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
