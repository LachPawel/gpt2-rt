import os
import json
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

load_dotenv()
app = FastAPI()

SESSION_CONFIG = {
    "type": "realtime",
    "model": "gpt-realtime-2",
    "audio": {"output": {"voice": "shimmer"}},
    "instructions": (
        "You are a friendly scheduling assistant. You can check calendar availability, "
        "book meetings, cancel meetings, and update contact names. "
        "When booking or cancelling, always confirm the details back to the user. "
        "Keep responses conversational but thorough when asked about rooms or schedules. "
        "When asked about available meeting rooms, describe several fictional rooms with "
        "capacity and floor numbers (e.g. Room A1 on floor 1 capacity 4, Room B2 on floor 2 "
        "capacity 10, Room C3 on floor 3 capacity 20). "
        "When asked about schedules, invent a plausible but brief week overview."
    ),
}


@app.get("/tasks")
async def get_tasks():
    with open("tasks.json") as f:
        return JSONResponse(content=json.load(f))


@app.get("/aic-license")
async def aic_license():
    return {"key": os.environ.get("AIC_SDK_LICENSE", "")}


@app.post("/session")
async def session(request: Request):
    sdp = (await request.body()).decode("utf-8")
    api_key = os.environ["OPENAI_API_KEY"]
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://api.openai.com/v1/realtime/calls",
            headers={"Authorization": f"Bearer {api_key}"},
            files={
                "sdp": (None, sdp),
                "session": (None, json.dumps(SESSION_CONFIG)),
            },
        )
    return Response(content=r.text, media_type="application/sdp", status_code=r.status_code)


@app.get("/")
async def index():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
