from fastapi import FastAPI
import asyncio
from run import main
from config.config import data_config

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/start-processing")
async def start_processing():
    asyncio.create_task(main(batch_size=data_config.batch_size))
    return {"status": "processing started"}
