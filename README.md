# Realtime Voice Agent in 60 Seconds

A tiny, opinionated starter for OpenAI's `gpt-realtime-2`. Two files do the work. The browser handles audio over WebRTC. Python forwards one handshake message with your API key attached. That's it.

```
You ─🎤─► Browser ═══════ audio + tool events ═══════ OpenAI Realtime
              │
              └── /session ── Python (40 lines, just adds the API key)
```

## What you get

- Voice in, voice out, real-time, low latency.
- Function calling. One JS object to add new tools.
- API key stays on the server. The browser never sees it.
- One env file controls model, voice, and system prompt.
- Production-friendly. Startup validation, health check, structured errors.
- No build step. No bundler. No frameworks.

## 60-second setup

```bash
git clone <this-repo> && cd gpt2-rt
cp .env.example .env             # paste your OPENAI_API_KEY
uv run --with-requirements requirements.txt python server.py
```

Open http://localhost:3000, click the mic, say "what time is it?" or "what's the weather where I am?".

Prefer pip?

```bash
pip install -r requirements.txt
python server.py
```

## How it works

1. Browser opens the mic and creates a WebRTC peer connection.
2. Browser POSTs its SDP offer to `/session`.
3. Python attaches `Authorization: Bearer $OPENAI_API_KEY` and forwards the offer to `https://api.openai.com/v1/realtime/calls` along with the session config (model, voice, instructions).
4. OpenAI returns its SDP answer. Python passes it back.
5. WebRTC peer connection opens directly between browser and OpenAI. Audio streams. A side data channel named `oai-events` carries JSON events (transcripts, tool calls).
6. When the model wants to call a tool, the browser runs the matching function in `TOOL_IMPL`, sends the result back, then triggers a response.

Python never touches audio. It is signaling only.

## Built-in tools

The starter ships three real tools, no extra API keys required:

- **`get_current_time`** uses the browser's locale and timezone. Try "what day is it?" or "what time is it in my timezone?".
- **`get_weather`** uses browser geolocation (with permission) and the free `wttr.in` service. Try "what's the weather where I am?" or "how warm is it in Tokyo?".
- **`see_screen`** captures your screen on demand and sends it to the model. Click **Share Screen**, then ask "what's on my screen?" or "help me with this". The model describes what it sees and guides you through the task.

## Add your own tool

Two places in [static/index.html](static/index.html):

```js
// 1. Describe the tool to the model
const TOOLS = [
  /* ...existing tools... */
  {
    type: "function",
    name: "flip_coin",
    description: "Flip a fair coin.",
    parameters: { type: "object", properties: {}, required: [] }
  }
];

// 2. Implement it. Return any JSON-serializable value. Async is fine.
const TOOL_IMPL = {
  /* ...existing impls... */
  flip_coin: () => ({ result: Math.random() < 0.5 ? "heads" : "tails" })
};
```

Reload, click the mic, ask the model to flip a coin. It figures out when to call the function.

## Change voice, model, or persona

Edit `.env`:

```
REALTIME_VOICE=ballad
REALTIME_MODEL=gpt-realtime-2
REALTIME_INSTRUCTIONS=You are a sarcastic concierge. Answer in one sentence.
```

Voices to try: `alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, `verse`.

## Health check

```
curl http://localhost:3000/healthz
{"ok":true,"model":"gpt-realtime-2","voice":"ash"}
```

## Production notes

- Put the server behind HTTPS in production. The browser already needs HTTPS for the mic unless you stay on `localhost`.
- `OPENAI_API_KEY` is validated at startup. Misconfig fails fast with a clear message.
- `/session` returns the upstream HTTP status if OpenAI rejects the request, so your monitoring picks it up.
- The server adds `Authorization` per request. Rotate the key in `.env` and restart. No code changes.
- Logs go to stdout in JSON-ish format. Pipe to your log aggregator of choice.

## File map

```
server.py          # FastAPI signaling server
static/index.html  # the entire frontend
requirements.txt   # fastapi, uvicorn, httpx, python-dotenv
.env.example       # copy to .env, add your key
```

## Extend further

- **More tools**: drop them into `TOOLS` and `TOOL_IMPL`. Async is fine.
- **Multiple voices/personas**: pass `instructions` and `voice` via `session.update` from the browser at runtime.
- **Transcripts**: the data channel already streams `response.audio_transcript.delta` events. Render them in the page.
- **Vision / screen capture**: click **Share Screen** to start a screen share. When you ask the model to look at your screen, the `see_screen` tool fires. It calls `ImageCapture.grabFrame()` on the screen share track, which pulls one decoded frame directly from the OS without needing a video element or any playback state. The frame is scaled to 1280px wide, encoded as JPEG, and injected into the conversation as an `input_image` message over the existing WebRTC data channel. No extra API call, no backend involved.
- **Robots, hardware, anything**: tool calls are just JavaScript. Hit a WebSocket, fire a webhook, call a serial port.

## License

MIT.
