# GPT Realtime 2 Voice Agent Demo

Minimal voice agent using OpenAI's Realtime API via WebRTC. Python serves signaling only — audio flows browser ↔ OpenAI directly.

## Setup

First, set your API key:

```
cp .env.example .env       # then edit .env and paste your OPENAI_API_KEY
```

### Run with uv (recommended)

```
uv run --with-requirements requirements.txt python server.py
```

Or with a persistent venv:

```
uv venv
uv pip install -r requirements.txt
uv run python server.py
```

### Run with pip

```
pip install -r requirements.txt
python server.py
```

Open http://localhost:3000 (mic requires HTTPS or localhost).

## Try it

Click the mic, then ask: *"Am I free Tuesday at 3pm?"* — the agent will call the `check_calendar` tool and speak the result.
