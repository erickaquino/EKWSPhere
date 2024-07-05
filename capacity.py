from fastapi import FastAPI
from pydantic import BaseModel
from mangum import Mangum

app = FastAPI()
handler = Mangum(app)


class DataModel(BaseModel):
    data: str


@app.get("/")
def index():
    return 'Hello Allyssa!!!!'


@app.post("/")
def processs_post(data: DataModel):
    return data


@app.post("/")
def processs_post(data: DataModel):
    return data


@app.post("/test/{data}")
def process_post(data):
    return data
