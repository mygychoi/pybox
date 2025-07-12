from fastapi import FastAPI

app = FastAPI()


@app.get("/.health-check")
def health_check() -> str:
    return "hello world"


@app.get("/echo")
def echo(q: str = "not provided") -> str:
    return q
