# Code exercise: rebooking assistant (LangGraph)

An assistant helps airline gate agents. It is a LangGraph graph in `assistant/graph.py` with three steps: find the
fare rules, ask the booking system for free seats, write the answer. The LLM is a fake one (`assistant/llm.py`), so
nothing needs an API key.

## Start

```bash
docker compose run --rm check
```

It prints one line per task, ✓ or ✗. Right now all three are ✗. The three tasks are independent: do them in any order.
You can use your usual AI assistant. Think out loud while you work.

To try the assistant: `docker compose run --rm check python ask.py "Is a cancelled flight free to change?" UA100`

## Task 1 (about 4 minutes)

When the booking system is down (flights starting with `UA9`), the graph retries forever and crashes. Make it try at
most 3 times, then answer without seats. Done: the answer says "I could not check seats right now."

## Task 2 (about 3 minutes)

The answer should list the ids of the passages it used, but `sources` is always empty. Done: `ask.py` prints the 3
passage ids.

## Task 3 (about 5 minutes)

In `assistant/retrieval.py`, write `recall_at_k` (its comment explains it), run
`docker compose run --rm check python evaluate.py`, and set `CHOSEN_RETRIEVER` to the better retriever.

## Rules

Do not change `check.py` or the `tests` folder. When you finish, commit, push to your repository and paste its link.

## Project layout (after the refactor)

| Path | What it holds |
|---|---|
| `assistant/graph.py` | Wires the graph; every dependency can be injected through `build(...)` |
| `assistant/nodes.py` | The nodes and the router, plus `Node` name constants |
| `assistant/models.py` | `State`, `Passage` and `EvalItem` types |
| `assistant/config.py` | `MAX_BOOKING_ATTEMPTS` and `TOP_K` |
| `assistant/retrieval.py` / `metrics.py` | The retrievers and `recall_at_k` |
| `assistant/alerts.py` | Where outages are reported (logs today) |
| `service.py`, `deploy/` | HTTP service and container/ECS Fargate setup (see `deploy/README.md`) |
| `unit_tests/` | Extra tests; `tests/` stays untouched for the exercise check |

```bash
docker compose run --rm check                                                  # exercise checks
docker compose run --rm check python -m unittest discover -s unit_tests -t .  # unit tests
docker build -f deploy/Dockerfile -t rebooking-assistant:local .               # service image
```
