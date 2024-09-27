from fastapi import FastAPI
from starlette.responses import RedirectResponse

app = FastAPI()

@app.get("/")
def read_root():
    return RedirectResponse("https://www.virtualpapertrading.com")
