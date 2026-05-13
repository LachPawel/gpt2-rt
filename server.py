"""
Minimal signaling server for OpenAI Realtime over WebRTC.

The browser handles audio. This server only forwards the SDP handshake
and attaches the API key, so the secret never leaves the backend.
"""
import json
import logging
import os
import sys

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    sys.exit("OPENAI_API_KEY is not set. Copy .env.example to .env and add your key.")

MODEL = os.environ.get("REALTIME_MODEL", "gpt-realtime-2")
VOICE = os.environ.get("REALTIME_VOICE", "ash")
INSTRUCTIONS = os.environ.get(
    "REALTIME_INSTRUCTIONS",
    (
        "You are a friendly, concise voice assistant. Keep replies short and conversational. "
        "You have the ability to look at the user's screen via the see_screen tool — use it "
        "whenever the user asks for help with something on their screen or wants guidance through a task. "
        "If they haven't shared their screen yet, tell them to click the Share Screen button first."
    ),
)

REALTIME_URL = "https://api.openai.com/v1/realtime/calls"

SESSION_CONFIG = {
    "type": "realtime",
    "model": MODEL,
    "audio": {"output": {"voice": VOICE}},
    "instructions": INSTRUCTIONS,
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("realtime")

app = FastAPI(title="Realtime Voice Agent")


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True, "model": MODEL, "voice": VOICE}


@app.post("/session")
async def session(request: Request) -> Response:
    """Forward the browser SDP offer to OpenAI and return their SDP answer."""
    sdp = (await request.body()).decode("utf-8")
    if not sdp.strip():
        raise HTTPException(status_code=400, detail="Empty SDP offer")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                REALTIME_URL,
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={
                    "sdp": (None, sdp),
                    "session": (None, json.dumps(SESSION_CONFIG)),
                },
            )
    except httpx.HTTPError as e:
        log.exception("Upstream call to OpenAI failed")
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}") from e

    if r.status_code >= 400:
        log.warning("OpenAI returned %s: %s", r.status_code, r.text[:200])
        raise HTTPException(status_code=r.status_code, detail=r.text)

    return Response(content=r.text, media_type="application/sdp")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse("static/index.html")






app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "3000"))
    log.info("Starting on http://localhost:%d (model=%s, voice=%s)", port, MODEL, VOICE)
    uvicorn.run(app, host="localhost", port=port)
