# PubSub Temporal Worker

A Temporal-based pub/sub system for event-driven workflow execution. This system provides a flexible event dispatching mechanism where producers publish events and consumers subscribe to specific event types.

## Requirements

### Prerequisites

- **Docker** (version 20.10+) and **Docker Compose** (version 2.0+)
- **Make** (for running convenience commands)
- **Python 3.13** (handled automatically via Docker)
- **uv** package manager (installed automatically in Docker)

### Environment Variables

The project uses environment variables with the `TEMPORAL_` prefix. Default values are set, but you can override them via a `.env` file:

- `TEMPORAL_ADDRESS` - Temporal server address (default: `localhost:7233`)
- `TEMPORAL_NAMESPACE` - Temporal namespace (default: `default`)
- `TEMPORAL_TASK_QUEUE` - Task queue name (default: `pubsub-task-queue`)

## Project Structure

```
pubsub/
├── consumers.py          # Consumer workflows that subscribe to events
├── producers.py          # Producer workflows that dispatch events
├── dispatchers.py       # Activity classes that handle event dispatching
├── events.py            # Event data models (EventPayload, EventDispatchInput)
├── registry.py         # Subscriber registry for event routing
├── registry_logger.py   # Workflow for logging registered workflows/activities
├── di.py                # Dependency injection configuration
├── worker.py            # Main worker entry point
└── temporal/
    ├── settings.py      # Temporal configuration
    └── utils.py         # Registration and discovery utilities
```

## How to Run

### 1. Start the Full Stack

Start all services (PostgreSQL, Temporal server, Temporal UI, admin tools, and worker):

```bash
make up
```

This will:
- Start PostgreSQL database (port 5432)
- Start Temporal server (port 7233)
- Start Temporal UI (port 8233)
- Start Temporal admin tools
- Build and start the worker

### 2. Auto-restart on Code Changes

Use watch mode to automatically restart the worker when code changes:

```bash
make watch
```

The worker will automatically restart when:
- Any files in `./pubsub` directory change
- `pyproject.toml` or `uv.lock` change (rebuilds container)
- `Dockerfile` changes (rebuilds container)
- `.env` file changes

### 3. View Logs

View all service logs:
```bash
make logs
```

View specific service logs:
```bash
make logs worker
make logs temporal
```

### 4. Stop Services

Stop all services:
```bash
make down
```

## How It Works

### Architecture Overview

The system uses Temporal workflows and activities to implement a pub/sub pattern:

1. **Producers** - Workflows that publish events
2. **Dispatchers** - Activities that route events to subscribers
3. **Consumers** - Workflows that subscribe to specific event types
4. **Registry** - Maintains a mapping of event types to consumer workflows

### Component Details

#### Event Models (`events.py`)

- **`EventPayload`**: Contains event data (`data: dict`)
- **`EventDispatchInput`**: Event dispatch request with:
  - `id`: Unique event identifier (UUID)
  - `event_type`: Type of event (e.g., "event.a", "event.b")
  - `payload`: Optional `EventPayload` object

#### Producer Workflows (`producers.py`)

Three types of producer workflows:

1. **`ProducerActivity`**: Dispatches events using `DispatchWithTemporalClient` activity
2. **`ProducerActivityRepeated`**: Calls the dispatch activity twice (for testing duplicate handling)
3. **`ProducerSignal`**: Dispatches events using `DispatchWithSignalAndStart` activity

#### Dispatcher Activities (`dispatchers.py`)

Two dispatch strategies:

1. **`DispatchWithTemporalClient`**:
   - Starts new consumer workflows directly
   - Workflow ID format: `{workflow_name}-{event_type}-{event_id}`
   - Uses `REJECT_DUPLICATE` policy to prevent duplicate workflows

2. **`DispatchWithSignalAndStart`**:
   - Starts workflows with a signal to existing workflows
   - Uses `start_signal="process_event"` to deliver events
   - Workflow ID format: `{workflow_name}-{event_type}-{event_id}`

#### Consumer Workflows (`consumers.py`)

Consumer workflows subscribe to events using the `@subscribe` decorator:

- **`ConsumerA`**: Subscribes to `"event.a"`
- **`ConsumerB`**: Subscribes to `"event.a"`
- **`ConsumerC`**: Subscribes to `"event.b"`

Each consumer:
- Has a `run` method that accepts `EventPayload | None`
- Has a `process_event` signal handler for receiving events
- Stores received events in instance state

#### Registration System (`temporal/utils.py`)

The system uses decorators and dynamic discovery:

- **`@register_workflow`**: Marks a class as a workflow (sets `__object_type__ = "workflow"`)
- **`@register_activity`**: Marks a class as an activity (sets `__object_type__ = "activity"`)
- **`@subscribe(event_type)`**: Marks a workflow as subscribing to an event type (sets `__subscribed_on__`)
- **`discover_objects()`**: Recursively scans the package to find workflows/activities
- **`get_workflows()`**: Returns all registered workflows
- **`get_activities()`**: Returns all registered activities

#### Subscriber Registry (`registry.py`)

- **`SubscriberRegistry`**: Maintains a mapping of event types to consumer workflows
- Created from discovered workflows by scanning for `__subscribed_on__` attribute
- Used by dispatchers to find subscribers for a given event type

#### Dependency Injection (`di.py`)

Uses `pydio` for dependency injection:
- Provides workflows list
- Provides activities list
- Provides `SubscriberRegistry` instance

### Event Flow

1. **Producer Workflow Starts**: A producer workflow (e.g., `ProducerActivity`) is triggered with an `EventDispatchInput`
2. **Dispatch Activity Executes**: The workflow calls a dispatcher activity (`DispatchWithTemporalClient` or `DispatchWithSignalAndStart`)
3. **Subscriber Lookup**: The dispatcher queries `SubscriberRegistry` for workflows subscribed to the event type
4. **Workflow Creation**: For each subscriber:
   - Creates a unique workflow ID: `{workflow_name}-{event_type}-{event_id}`
   - Starts the consumer workflow with the event payload
   - Uses `REJECT_DUPLICATE` policy to prevent duplicates
5. **Consumer Processing**: Consumer workflows receive and process the events

### Triggering Workflows

#### Start ProducerActivity

```bash
make wf-producer-activity EVENT_TYPE=event.a
```

This will:
- Generate a random UUID for the event ID
- Start `ProducerActivity` workflow
- Dispatch event to all subscribers of `event.a` (ConsumerA, ConsumerB)

#### Start ProducerActivityRepeated

```bash
make wf-producer-activity-repeated EVENT_TYPE=event.a
```

This will dispatch the same event twice, useful for testing duplicate handling.

#### Start ProducerSignal

```bash
make wf-producer-signal EVENT_TYPE=event.b
```

This will dispatch event to subscribers using signal-based delivery.

#### View Registry

```bash
make wf-registry-logger
```

This will log all registered workflows, activities, and event subscriptions.

## Accessing Temporal UI

Once the stack is running, access the Temporal UI at:

```
http://localhost:8233
```

You can:
- View running workflows
- Monitor workflow execution history
- Debug workflow issues
- View activity executions

## Development

### Code Style

The project uses `ruff` for linting and formatting. Settings are in `pyproject.toml`.

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pre-commit install
```

Hooks will automatically run `ruff` on commit to ensure code quality.

## Example Usage

1. Start the stack:
   ```bash
   make up
   ```

2. Trigger an event:
   ```bash
   make wf-producer-activity EVENT_TYPE=event.a
   ```

3. Check logs to see consumers processing:
   ```bash
   make logs worker
   ```

4. View in Temporal UI:
   - Open http://localhost:8233
   - Search for workflow `ProducerActivity`
   - See child workflows `ConsumerA` and `ConsumerB` being created
