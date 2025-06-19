from fastapi import FastAPI
import asyncio
from run import main
from config.config import data_config


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
        finally:
            is_running = False

    asyncio.create_task(wrapped_main())

    return {"status": "processing started"}

@app.get("/status")
def status():
    return {"running": is_running}

