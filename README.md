# AI Tutor Model Service

A small Python service that wraps the Gemini API to power a multi-subject AI
tutor ("Paul"). It teaches: English Language, Oral English, Written English,
Public Speaking & Presentation, Igbo Language, and Igbo Culture — all through
a single chat-style endpoint.

This service does **not** have a UI and does **not** store any data. It is
stateless: you send it conversation history on every request, it sends back
one reply. All session/user storage is your responsibility on the backend.

---

## Quick Start (TL;DR for backend integration)

You only need one endpoint: **`POST /chat`**.

```
POST /chat
Content-Type: application/json

{
  "history": [
    {"role": "user", "text": "Hi"},
    {"role": "model", "text": "Hello! Which subject would you like to learn?"}
  ],
  "message": "Igbo language please"
}
```

Response:
```json
{
  "reply": "Sure — switching to Igbo Language! Before we dive in, would you say you're just starting out, comfortable but want to improve, or fairly advanced?"
}
```

That's the whole contract. Read on for details, setup, and error handling.

---

## API Reference

### `POST /chat`

Sends a learner's message (plus prior conversation) and gets the tutor's next reply.

**Request body:**

| Field     | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `history` | array  | No (defaults to `[]`) | Every prior turn in the conversation, **oldest first**. Empty on the very first message of a session. |
| `message` | string | Yes | The learner's new message. |

Each item in `history` looks like:
```json
{ "role": "user", "text": "..." }
```
or
```json
{ "role": "model", "text": "..." }
```
`role` must be exactly `"user"` or `"model"` (these are Gemini's role names —
`"model"` represents the tutor's previous replies, not `"assistant"` or `"ai"`).

**Response body:**

| Field   | Type   | Description |
|---------|--------|--------------|
| `reply` | string | The tutor's reply. Plain text — may contain `\n` line breaks (e.g. when listing the 6 subjects), render accordingly. |

**Critical integration requirement — conversation history:**
This service has no memory of its own. On every single call, your backend
must send back the *entire* conversation so far in `history`, then append
the new `message`. If you only ever send the latest message with an empty
`history`, the tutor will lose all context — it won't remember the subject
the learner picked, their stated skill level, or anything previously said.

Practically: after each `/chat` call, take the `message` you sent **and** the
`reply` you got back, and append both to your stored history for that
session, in order, before the next call.

### `GET /health`

Simple liveness check. Returns `{"status": "ok"}` with no auth required. Use
this for uptime monitoring or deployment platform health checks — it does
**not** call Gemini, so it won't tell you if the Gemini API key is invalid,
only that this service's process is running.

---

## Error Handling

| Status | Meaning | What to do |
|--------|---------|------------|
| `400`  | `message` was empty or missing | Validate on your end before calling; this is a request bug, not transient. |
| `422`  | Request body didn't match the expected shape (e.g. missing `message` field, wrong type) | Check your request body against the contract above. |
| `502`  | The call to Gemini failed | See below — **this can be transient, worth retrying.** |

### About 502 errors specifically

The most common cause of a `502` is Gemini's API returning a `503 UNAVAILABLE`
("model is experiencing high demand") — this happens occasionally on the free
tier under load, and is **not a bug in this service**. It's expected, fairly
common, and almost always resolves itself within seconds.

**Recommendation:** if you receive a `502` from `/chat`, retry the same
request once or twice with a short delay (e.g. 1-2 seconds) before showing
the learner an error. Do not retry indefinitely — if it fails 3 times in a
row, something else may be wrong and it's worth surfacing a "please try again
in a moment" message to the user rather than silently retrying forever.

This service does not currently implement retry logic internally — that
decision is left to the caller (you), since you're better positioned to
decide how many retries fit your UX.

---

## Local Setup (only needed if you want to run this yourself)

If you're just calling the hosted version of this service, you can skip this
section entirely — you only need the URL and the `/chat` contract above.

**Requirements:** Python 3.10+, a Gemini API key (from
[Google AI Studio](https://aistudio.google.com/apikey)).

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Gemini API key as an environment variable
#    Windows (cmd):
set GEMINI_API_KEY=your-actual-key-here
#    Mac/Linux:
export GEMINI_API_KEY=your-actual-key-here

# 3. Start the server
uvicorn main:app --reload --port 8000
```

The service will be available at `http://127.0.0.1:8000`. Test it with:

```bash
curl http://127.0.0.1:8000/health
```

**Note:** the environment variable above only persists for the current
terminal session — you'll need to set it again each time you open a new
terminal, unless you set it as a permanent system environment variable or use
a `.env` file.

---

## Project Structure

| File | Purpose |
|------|---------|
| `system_prompt.py` | The full instruction set that defines the tutor's behavior, personality, and rules for all 6 subjects. Pure text, no logic. |
| `tutor_model.py` | Core logic — connects to the Gemini API, converts conversation history into Gemini's expected format, and returns replies. Can be used standalone without any HTTP server (see `test_locally.py`). |
| `main.py` | The HTTP server (FastAPI) — exposes `tutor_model.py`'s logic as the `/chat` and `/health` endpoints described above. This is what you actually call. |
| `test_locally.py` | A terminal-based chat loop for manually testing the tutor without needing the HTTP server running. Not used in production — a development convenience only. |
| `requirements.txt` | Python dependencies. |

---

## Known Limitations (be aware of these)

- **No built-in memory** — see the "Critical integration requirement" note
  above. The service is intentionally stateless; all history management is
  the caller's responsibility.
- **No authentication** — this service currently has no API key or auth check
  of its own on the `/chat` endpoint. Anyone who can reach the URL can call
  it. If this is deployed somewhere publicly reachable, you may want to add
  your own auth layer in front of it (e.g. an API key check, or only allowing
  calls from your backend's IP/network).
- **CORS is currently wide open** (`allow_origins=["*"]` in `main.py`) for
  development convenience. This should be restricted to your backend's actual
  domain before going to production — flagged with a `TODO` comment in the
  code.
- **Igbo language/culture content accuracy is not guaranteed.** The tutor is
  instructed to express uncertainty rather than invent information, but it is
  using Gemini's general knowledge, not a verified curriculum. Treat Igbo
  content as a helpful starting point, not an authoritative source, until
  spot-checked.
- **No rate limiting** — if many users hit this simultaneously, Gemini's free
  tier may throttle or return more frequent `503`s. There is currently no
  queueing or backoff logic.
