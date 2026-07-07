from __future__ import annotations
from dotenv import load_dotenv
import asyncio
import copy
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from meeting_state import MeetingState
from orchestrator import Orchestrator
from simulator import SCENARIOS

load_dotenv()
app = FastAPI(title="Candidate Identification")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/scenarios")
def list_scenarios():
    return [
        {"id": key, "title": s["title"], "description": s["description"]}
        for key, s in SCENARIOS.items()
    ]


@app.websocket("/ws/run/{scenario_id}")
async def run_scenario(websocket: WebSocket, scenario_id: str, speed: float = 4.0):
    await websocket.accept()
    scenario = SCENARIOS.get(scenario_id)
    if not scenario:
        await websocket.send_json({"error": f"unknown scenario '{scenario_id}'"})
        await websocket.close()
        return

    meta = copy.deepcopy(scenario["meta"])
    state = MeetingState(meta=meta)
    orchestrator = Orchestrator(state)

    try:
        last_t = 0.0
        for event in scenario["events"]:
            wait = max(0.0, (event["t"] - last_t) / speed)
            await asyncio.sleep(wait)
            last_t = event["t"]
            live_event = dict(event)
            live_event["t"] = time.time()
            snapshot = orchestrator.apply_event(live_event)
            await websocket.send_json(snapshot)

        await websocket.send_json({"done": True})
    except WebSocketDisconnect:
        return


app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
