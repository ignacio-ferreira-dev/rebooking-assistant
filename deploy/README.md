# Deploying the rebooking assistant

`service.py` wraps the graph in a small HTTP API (stdlib only, no new dependencies):

| Endpoint | Purpose |
|---|---|
| `GET /health` | Load balancer and container health check |
| `POST /ask` `{"question": "...", "flight": "UA100"}` | Returns `{"answer", "sources", "booking_available"}` |

## Run it locally like Fargate would

```bash
docker build -f deploy/Dockerfile -t rebooking-assistant:local .
docker run --rm --read-only --tmpfs /tmp -p 8080:8080 rebooking-assistant:local

curl localhost:8080/health
curl -X POST localhost:8080/ask -d '{"question": "Is a cancelled flight free to change?", "flight": "UA100"}'
```

What the image does for a container platform:
- Runs as a non-root user (uid 10001) and works with a read-only root filesystem.
- Has a `HEALTHCHECK` on `/health`.
- Python is PID 1, so it gets `SIGTERM` and shuts down cleanly (exit code 0) during deploys and scale-in.
- Logs one JSON object per line to stdout, which the `awslogs` driver ships to CloudWatch.

## Deploy to ECS Fargate (outline)

1. Push the image to ECR, tagged with the git SHA (immutable tags):
   ```bash
   aws ecr get-login-password | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com
   docker tag rebooking-assistant:local <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/rebooking-assistant:<GIT_SHA>
   docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/rebooking-assistant:<GIT_SHA>
   ```
2. Fill in the placeholders in `ecs-task-definition.json` and register it:
   `aws ecs register-task-definition --cli-input-json file://deploy/ecs-task-definition.json`
3. Create a service behind an ALB (target group health check: `GET /health`) in private subnets, with the
   **deployment circuit breaker and rollback** enabled.

IAM: the **execution role** pulls the image and writes logs. The **task role** is what the code can call. Today it
needs nothing; when the fake LLM is replaced by Bedrock, grant only `bedrock:InvokeModel` on that model's ARN.

## Production follow-ups (not in this repo)
- Replace `alerts.notify` (log only) with SNS or PagerDuty, and alarm on the `rebooking.alerts` log level `ERROR`.
- Replace the fake LLM (`assistant/llm.py`) and the booking stub (`assistant/booking.py`) with real clients.
- Add a checkpointer (`PostgresSaver` on RDS) only if conversations need to persist or resume across requests.
