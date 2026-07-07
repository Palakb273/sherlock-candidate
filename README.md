# 🔍 Candidate Identification Engine

> **Real-time interview fraud detection using an event-driven multi-agent system.**

This watches a live video-interview meeting and continuously answers the question: *who is the actual candidate?* A pool of independent signal agents vote on every participant's likelihood of being the candidate; a fusion agent arbitrates their votes and explains its reasoning — all updating live as the meeting unfolds.

---

## ✨ Features

- **Live confidence scoring** — every meeting event (join, speech, webcam, name change) re-triggers all agents and instantly updates participant scores
- **Multi-agent architecture** — four independent signal agents cover different evidence channels, making the system robust to any single channel failing
- **LLM-augmented transcript analysis** — optionally uses Groq (`llama-3.3-70b-versatile`) for accurate name extraction from spoken text, with a regex fallback when no API key is present
- **Five built-in demo scenarios** covering the trickiest real-world edge cases
- **WebSocket-driven UI** — no polling; the browser receives snapshots as fast as they are produced
- **Adjustable simulation speed** — replay at 1x, 4x, or 10x to demo quickly or study carefully

---

## Architecture

```
Browser (WebSocket client)
        │
        ▼
┌──────────────────────────────────┐
│  FastAPI  /ws/run/{scenario_id}  │
│  (main.py)                       │
└─────────────┬────────────────────┘
              │ event stream
              ▼
┌──────────────────────────────────┐
│         Orchestrator             │
│  1. _mutate_state(event)         │
│  2. run all signal agents        │
│  3. fusion.fuse(state, evidence) │
│  4. return snapshot JSON         │
└───┬──────────────────────────────┘
    │
    ├──► MetadataMatchAgent    (weight 0.35)
    ├──► TranscriptSignalAgent (weight 0.55)
    ├──► BehavioralSignalAgent (weight 0.30)
    ├──► JoinPatternAgent      (weight 0.15)
    │
    └──► FusionAgent  (softmax over raw scores → confidence %)
```

---

## Signal Agents

### 1. Metadata Match Agent (`agents/metadata_agent.py`)

Compares each participant's display name against the **candidate name and email** pulled from the calendar/ATS invite.

| Signal | Score |
|--------|-------|
| Display name closely matches candidate record | +0.60 to +1.00 |
| Weak / partial name overlap | +0.00 to +0.30 |
| Matches a known interviewer name | -0.80 |
| Name looks like a device name (e.g. "MacBook Pro") | 0.00 (low weight) |

### 2. Transcript Signal Agent (`agents/transcript_agent.py`)

Reads the live, **speaker-attributed** transcript for direct identity evidence.

| Signal | Score |
|--------|-------|
| Self-introduction matching candidate name | +0.95 |
| Partial self-introduction match | +0.75 |
| Addressed by another participant using candidate's name | +0.75 |
| Self-introduction that does not match | -0.30 |

Uses **Groq (`llama-3.3-70b-versatile`)** for extraction when `GROQ_API_KEY` is set; falls back to regex patterns when the key is absent.

### 3. Behavioral Signal Agent (`agents/behavioral_agent.py`)

Observes **non-linguistic presence signals** — who talks the most, webcam state, and screen sharing.

| Signal | Score |
|--------|-------|
| >= 40% of total speaking time | +0.50 |
| Webcam is on | +0.15 |
| Currently screen-sharing | +0.10 |
| Only <= 10% of speaking time | -0.30 |
| Has not spoken at all (silent observer) | -0.60 |

### 4. Join Pattern Agent (`agents/join_pattern_agent.py`)

Checks whether each participant **joined near the scheduled interview time** (within ±5 minutes).

| Signal | Score |
|--------|-------|
| Joined within 5 min of scheduled start | +0.20 |
| Joined well outside the scheduled window | -0.10 |

---

## Fusion Agent (`agents/fusion_agent.py`)

Aggregates all `Evidence` objects via a **softmax** over weighted raw scores and applies two thresholds:

| Status | Condition |
|--------|-----------|
| `confident` | Top participant >= 45% confidence **and** >= 30 pp margin over second place |
| `ambiguous` | Top participant >= 31% but margin too narrow |
| `insufficient_data` | No strong signal yet or only interviewers present |

---

## Demo Scenarios

| ID | Title | What it tests |
|----|-------|---------------|
| `device_name` | Candidate joins as "MacBook Pro" | Metadata agent gives zero signal; identity resolves from transcript self-intro |
| `nickname` | Candidate joins as "Rii" | Weak name match; interviewer addressing candidate by real name confirms identity |
| `wrong_invite_name` | Invite says "Ritika Sharma", candidate is Riya Sharma | Fuzzy name similarity across a typo in the ATS |
| `multiple_observers` | Two silent guests join | Silent-observer penalty isolates the real candidate |
| `name_change_midcall` | Candidate starts as "DESKTOP-88AJ2", renames to "Riya S." | Identity persistence across a display-name change mid-call |

---

## Project Structure

```
sherlock-id/
├── backend/
│   ├── main.py                   # FastAPI app, WebSocket endpoint, static file mount
│   ├── orchestrator.py           # Event processing pipeline and agent runner
│   ├── meeting_state.py          # MeetingState + ExternalMetadata dataclasses
│   ├── simulator.py              # Five pre-built demo scenarios
│   ├── requirements.txt
│   ├── .env                      # GROQ_API_KEY (git-ignored)
│   └── agents/
│       ├── base.py               # Evidence + ParticipantSnapshot + Agent base class
│       ├── metadata_agent.py     # Display-name vs ATS record matching
│       ├── transcript_agent.py   # Self-intro & address-name extraction (LLM + regex)
│       ├── behavioral_agent.py   # Speaking time, webcam, screen-share signals
│       ├── join_pattern_agent.py # Join-timing vs. scheduled start
│       └── fusion_agent.py       # Softmax fusion + status / explanation
└── frontend/
    └── index.html                # Single-page UI (vanilla HTML/CSS/JS, WebSocket client)
```

---

## Assumptions

- The platform (Meet/Teams/Zoom) already exposes, per the brief: participant
  join/leave events, per-participant audio streams with speaking activity/duration,
  per-participant webcam video, a speaker-attributed transcript, and external
  metadata (candidate name/email, calendar invite, interviewer names). This
  prototype consumes exactly that shape of data — nothing more.
- The transcript agent's LLM calls are single, short, targeted extractions
  ("did this snippet contain a self-introduction, and what name?"), not open-ended
  reasoning — this keeps latency and cost low enough for near-real-time use per
  utterance.
- Video-based signals (face matching to an ID photo, lip-sync/deepfake detection)
  are out of scope for this prototype's agents but are the natural next agent to
  add — the fusion layer already supports it without any redesign.
- "Real time" here means "reacts to each new event within the same pipeline
  tick," not literal sub-second production latency — the simulator's playback
  speed is just for demo pacing.


## Getting Started

### Prerequisites

- Python 3.10+
- (Optional) A [Groq API key](https://console.groq.com/) for LLM-powered transcript extraction

### 1. Clone and install

```bash
git clone https://github.com/your-org/sherlock-id.git
cd sherlock-id/backend
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file inside `backend/`:

```env
GROQ_API_KEY=gsk_...   # optional — regex fallback is used when absent
```

### 3. Run the server

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The frontend is served automatically at **http://127.0.0.1:8000**.
Open it in your browser, pick a scenario from the sidebar, and watch the agents reason in real time.

---

## API Reference

### `GET /api/scenarios`

Returns the list of available simulation scenarios.

```json
[
  {
    "id": "device_name",
    "title": "Candidate joins as MacBook Pro",
    "description": "Display name gives zero signal; identity resolves once the transcript starts."
  }
]
```

### `WS /ws/run/{scenario_id}?speed={float}`

Streams a real-time simulation. Each WebSocket message is a snapshot JSON object:

```json
{
  "event": { "type": "speech", "participant_id": "p2", "text": "Hi, my name is Riya..." },
  "status": "confident",
  "selected_participant_id": "p2",
  "explanation": "Identified Riya Sharma as the candidate with 91% confidence. Key evidence: ...",
  "participants": [
    {
      "participant_id": "p2",
      "display_name": "Riya Sharma",
      "confidence": 0.912,
      "raw_score": 1.847,
      "top_reasons": [
        "Self-introduced as Riya Sharma, matching candidate record.",
        "Accounts for 72% of all speaking time.",
        "Display name matches candidate record with similarity 1.00."
      ]
    }
  ]
}
```

The final message when the simulation ends is `{ "done": true }`.

**Query parameter:** `speed` (default `4.0`) — playback multiplier. `4.0` replays events 4x faster than real-time.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | (unset) | Enables LLM-based name extraction in the transcript agent. Regex fallback is used when absent. |

---

## Scalability

### Adding a new signal agent

1. Create `backend/agents/my_agent.py` subclassing `Agent` from `base.py`
2. Implement `analyze(self, state: MeetingState) -> list[Evidence]`
3. Register it in `orchestrator.py`:

```python
from agents.my_agent import MyAgent

class Orchestrator:
    def __init__(self, state):
        self.agents = [
            MetadataMatchAgent(),
            TranscriptSignalAgent(),
            BehavioralSignalAgent(),
            JoinPatternAgent(),
            MyAgent(),          # add here
        ]
```

### Adding a new scenario

Add an entry to the `SCENARIOS` dict in `backend/simulator.py`:

```python
SCENARIOS["my_scenario"] = {
    "title": "Short display title",
    "description": "One-line description shown in the sidebar.",
    "meta": ExternalMetadata(
        candidate_name="Jane Doe",
        candidate_email="jane@example.com",
        interviewer_names=["Alice"],
        scheduled_start_epoch=time.time(),
    ),
    "events": [
        {"t": 0,  "type": "join",   "participant_id": "p1", "display_name": "Alice"},
        {"t": 2,  "type": "join",   "participant_id": "p2", "display_name": "Jane Doe"},
        {"t": 10, "type": "speech", "participant_id": "p2", "duration_sec": 5,
         "text": "Hi, I am Jane Doe, excited for this interview."},
    ],
}
```

---

## License

MIT
