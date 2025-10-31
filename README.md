# PubSub Temporal Worker

A Temporal-based pub/sub system for event-driven workflow execution.

## Development

### Prerequisites

- Docker and Docker Compose
- Make

### Running the Stack

Start all services:
```bash
make up
```

Start only the worker:
```bash
make worker
```

Restart the worker after code changes:
```bash
make worker-restart
```

### Auto-restart on Changes

When using `docker compose watch` (via `make watch`), the worker container will automatically restart when:
- Any files in `./pubsub` directory change
- `pyproject.toml` or `uv.lock` change (rebuilds container)
- `Dockerfile` changes (rebuilds container)
- `.env` file changes

**Note**: After any change to worker code (`pubsub/worker.py` or any files in `pubsub/`), the worker container will automatically restart if you're using `make watch`. Otherwise, manually restart with `make worker-restart`.

### Triggering Workflows

Start ProducerActivity:
```bash
make wf-producer-activity EVENT_TYPE=event.a
```

Start ProducerWorkflow:
```bash
make wf-producer-workflow EVENT_TYPE=event.b
```

Start ProducerSignal:
```bash
make wf-producer-signal EVENT_TYPE=event.a
```

### Viewing Logs

View all logs:
```bash
make logs
```

View worker logs:
```bash
make logs worker
```

