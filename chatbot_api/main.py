from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import conversation
from pydantic import BaseModel


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_methods=["*"],
    allow_headers=["*"],
)


class Image(BaseModel):
    file: bytes


@app.get("/")
def health():
    return {"health": "OK !"}


app.include_router(conversation.router)
