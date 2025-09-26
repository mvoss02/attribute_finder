import asyncio

from fastapi import FastAPI

from src.config.config import data_config
from src.run import main

app = FastAPI()
is_running = False  # shared app-level state

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/start-processing")
async def start_processing():
    global is_running

    if is_running:
        return {"status": "already running"}

    is_running = True

    async def wrapped_main():
        global is_running
        try:
            await main(batch_size=data_config.batch_size)
            return {"status": "processing started"}
        finally:
            is_running = False

    asyncio.create_task(wrapped_main())

    return {"status": "done"}

@app.get("/status")
def status():
    return {"running": is_running}
