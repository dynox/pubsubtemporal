# PubSub Temporal Worker

A Temporal-based pub/sub system for event-driven workflow execution with domain-based architecture. This system provides a flexible event dispatching mechanism where producers publish events and consumers subscribe to specific event types across multiple isolated workers.

## Requirements

### Prerequisites

- **Docker** (version 20.10+) and **Docker Compose** (version 2.0+)
- **Make** (for running convenience commands)
- **Python 3.13** (handled automatically via Docker)
- **uv** package manager (installed automatically in Docker)

### Environment Variables

The project uses environment variables with the `TEMPORAL_` prefix. Configure them via the `.env` file:

```env
TEMPORAL_ADDRESS=temporal:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_TASK_QUEUE=pubsub-task-queue
TEMPORAL_TASK_QUEUE_SECONDARY=pubsub-task-queue-secondary
```

## Project Structure

```
pubsub/
├── domain_a/                    # Primary domain
│   ├── consumers.py             # ConsumerA, ConsumerC
│   └── producers.py             # Producer workflow
├── domain_b/                    # Secondary domain (isolated)
│   └── consumers.py             # ConsumerB
├── common/                      # Shared infrastructure
│   └── dispatchers.py           # Dispatcher workflow and activity
├── temporal/                    # Temporal utilities
│   ├── settings.py              # Configuration
│   └── utils.py                 # Registration and discovery
├── events.py                    # Event data models
├── registry.py                  # Subscriber registry
├── registry_logger.py           # Registry logging workflow
├── di.py                        # Dependency injection
├── worker.py                    # Primary worker (domain_a + common)
└── worker_secondary.py          # Secondary worker (domain_b)
```

## Architecture Overview

### Multi-Worker Design

The system uses **two independent workers** with domain isolation:

#### Primary Worker (`worker.py`)
- **Task Queue**: `pubsub-task-queue`
- **Loads**: `domain_a` + `common`
- **Workflows**: ConsumerA, ConsumerC, Producer, Dispatcher
- **Activities**: DispatcherActivity
- **Purpose**: Main event processing and dispatching

#### Secondary Worker (`worker_secondary.py`)
- **Task Queue**: `pubsub-task-queue-secondary`
- **Loads**: `domain_b` only
- **Workflows**: ConsumerB
- **Activities**: None
- **Purpose**: Isolated processing for domain_b workflows

### Domain Architecture

**Domain A** - Primary domain with producers and consumers
- Producer workflow for publishing events
- ConsumerA and ConsumerC for event processing

**Domain B** - Isolated domain with independent consumers
- ConsumerB with custom task queue routing
- Runs on separate worker for isolation

**Common** - Shared infrastructure
- Dispatcher workflow and activity
- Used by domain_a producers

## How to Run

### 1. Start the Full Stack

Start all services (PostgreSQL, Temporal server, Temporal UI, admin tools, and both workers):

```bash
make up
```

This will:
- Start PostgreSQL database (port 5432)
- Start Temporal server (port 7233)
- Start Temporal UI (port 8233)
- Start Temporal admin tools
- Build and start primary worker
- Build and start secondary worker

### 2. Auto-restart on Code Changes

Use watch mode to automatically restart workers when code changes:

```bash
make watch
```

Both workers will automatically restart when:
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
make logs worker-secondary
make logs temporal
```

### 4. Stop Services

Stop all services:
```bash
make down
```

## Component Details

### Event Models (`events.py`)

- **`EventPayload`**: Contains event data (`data: dict`)
- **`EventDispatchInput`**: Event dispatch request with:
  - `id`: Unique event identifier (UUID)
  - `event_type`: Type of event (e.g., "event.a", "event.b")
  - `payload`: Optional `EventPayload` object

### Producer Workflow (`domain_a/producers.py`)

```python
@register_workflow
@workflow.defn
class Producer:
    async def run(self, args: EventDispatchInput) -> None:
        # Starts Dispatcher workflow to route events
        await workflow.execute_child_workflow(Dispatcher.run, args=(args,))
```

### Dispatcher (`common/dispatchers.py`)

**Dispatcher Workflow** - Coordinates event dispatching

**DispatcherActivity** - Routes events to subscribers:
1. Queries `SubscriberRegistry` for workflows subscribed to the event type
2. For each subscriber:
   - Reads custom task queue from `__task_queue__` attribute (if set)
   - Falls back to default task queue from settings
   - Creates unique workflow ID: `{workflow_name}-{event_type}-{event_id}`
   - Starts consumer workflow with the event payload
   - Uses `REJECT_DUPLICATE` policy to prevent duplicates

### Consumer Workflows

#### Domain A Consumers (`domain_a/consumers.py`)

```python
@subscribe("event.a")
@workflow.defn
class ConsumerA:
    async def run(self, args: EventPayload | None = None) -> None:
        # Process event.a events on primary worker
        ...

@subscribe("event.b")
@workflow.defn
class ConsumerC:
    async def run(self, args: EventPayload | None = None) -> None:
        # Process event.b events on primary worker
        ...
```

#### Domain B Consumer (`domain_b/consumers.py`)

```python
@subscribe("event.a", task_queue="pubsub-task-queue-secondary")
@workflow.defn
class ConsumerB:
    async def run(self, args: EventPayload | None = None) -> None:
        # Process event.a events on secondary worker
        ...
```

### Custom Task Queue Routing

The `@subscribe` decorator supports custom task queue configuration:

```python
# Default task queue (from settings)
@subscribe("event.a")
class ConsumerA:
    ...

# Custom task queue
@subscribe("event.a", task_queue="custom-queue")
class ConsumerB:
    ...
```

When dispatching events, the `DispatcherActivity` reads the `__task_queue__` attribute:
- If set: Uses the custom task queue
- If not set: Falls back to `settings.task_queue`

### Registration System (`temporal/utils.py`)

The system uses decorators and dynamic discovery:

- **`@register_workflow`**: Marks a class as a workflow
- **`@register_activity`**: Marks a class as an activity
- **`@subscribe(event_type, task_queue=None)`**: Marks a workflow as subscribing to an event type with optional custom task queue
- **`discover_objects(package, object_type)`**: Recursively scans the package to find workflows/activities
- **`get_workflows(package)`**: Returns all registered workflows in a package
- **`get_activities(package)`**: Returns all registered activities in a package

### Subscriber Registry (`registry.py`)

- **`SubscriberRegistry`**: Maintains a mapping of event types to consumer workflows
- Created from discovered workflows by scanning for `__subscribed_on__` attribute
- Used by dispatchers to find subscribers for a given event type

### Worker Configuration (`worker.py`)

The `run_worker_with_packages()` function provides parameterized worker setup:

```python
async def run_worker_with_packages(
    workflow_packages: list[str],      # Packages to load workflows from
    activity_packages: list[str],      # Packages to load activities from
    task_queue: str,                   # Task queue name
) -> None:
    # Discovers and registers workflows/activities
    # Starts worker with specified configuration
    ...
```

Both workers use this shared function with different configurations:

```python
# Primary worker
await run_worker_with_packages(
    workflow_packages=["pubsub.domain_a", "pubsub.common"],
    activity_packages=["pubsub.domain_a", "pubsub.common"],
    task_queue=settings.task_queue,
)

# Secondary worker
await run_worker_with_packages(
    workflow_packages=["pubsub.domain_b"],
    activity_packages=["pubsub.domain_b"],
    task_queue=settings.task_queue_secondary,
)
```

## Event Flow

### Publishing an Event

1. **Producer Workflow Starts**: `Producer` workflow is triggered with an `EventDispatchInput`
2. **Dispatcher Workflow Executes**: Producer calls `Dispatcher.run()` as a child workflow
3. **Dispatcher Activity Runs**: Dispatcher executes `DispatcherActivity.run()`
4. **Subscriber Lookup**: Activity queries `SubscriberRegistry` for workflows subscribed to the event type
5. **Task Queue Resolution**: For each subscriber:
   - Checks if workflow has custom `__task_queue__` attribute
   - Falls back to default task queue if not set
6. **Workflow Creation**: For each subscriber:
   - Creates unique workflow ID: `{workflow_name}-{event_type}-{event_id}`
   - Starts consumer workflow on the appropriate task queue
   - Uses `REJECT_DUPLICATE` policy to prevent duplicates
7. **Consumer Processing**: Consumer workflows receive and process events on their respective workers

### Example: Publishing event.a

```
Producer (domain_a)
    ↓
Dispatcher (common)
    ↓
DispatcherActivity (common)
    ↓
    ├─→ ConsumerA (domain_a, task_queue: pubsub-task-queue) → Primary Worker
    └─→ ConsumerB (domain_b, task_queue: pubsub-task-queue-secondary) → Secondary Worker
```

## Triggering Workflows

### Start Producer Workflow

```bash
make wf-producer EVENT_TYPE=event.a
```

This will:
- Generate a random UUID for the event ID
- Start `Producer` workflow
- Dispatch event to all subscribers of `event.a`:
  - ConsumerA (on primary worker)
  - ConsumerB (on secondary worker)

You can also trigger `event.b`:
```bash
make wf-producer EVENT_TYPE=event.b
```

This dispatches to ConsumerC (on primary worker).

### View Registry

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
- Filter by task queue to see worker-specific workflows

## Development

### Adding a New Consumer

1. Choose the appropriate domain package (`domain_a` or `domain_b`)
2. Create a new consumer class:

```python
@subscribe("event.new", task_queue="custom-queue")  # optional task_queue
@workflow.defn
class NewConsumer:
    @workflow.run
    async def run(self, args: EventPayload | None = None) -> None:
        # Process event
        ...
```

3. The worker will automatically discover and register the new consumer
4. No worker restart needed in watch mode

### Adding a New Domain

1. Create new package: `pubsub/domain_c/`
2. Add `__init__.py` and consumer/producer files
3. Create new worker file or update existing worker:

```python
await run_worker_with_packages(
    workflow_packages=["pubsub.domain_c"],
    activity_packages=["pubsub.domain_c"],
    task_queue="pubsub-task-queue-custom",
)
```

4. Add worker to `docker-compose.yml`

### Code Style

The project uses `ruff` for linting and formatting. Settings are in `pyproject.toml`.

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pre-commit install
```

Hooks will automatically run `ruff` on commit to ensure code quality.

## Example Usage

### Basic Event Flow

1. Start the stack:
   ```bash
   make up
   ```

2. Trigger an event:
   ```bash
   make wf-producer EVENT_TYPE=event.a
   ```

3. Check logs to see consumers processing on different workers:
   ```bash
   # Primary worker (ConsumerA)
   make logs worker

   # Secondary worker (ConsumerB)
   make logs worker-secondary
   ```

4. View in Temporal UI:
   - Open http://localhost:8233
   - Search for workflow `Producer`
   - See child workflows:
     - `Dispatcher` (on primary worker)
     - `ConsumerA` (on primary worker, task queue: pubsub-task-queue)
     - `ConsumerB` (on secondary worker, task queue: pubsub-task-queue-secondary)

### Observing Worker Startup

When workers start, they log discovered workflows and activities with module paths:

**Primary Worker:**
```
Worker loading from packages: workflows=['pubsub.domain_a', 'pubsub.common'], activities=['pubsub.domain_a', 'pubsub.common']
Worker task queue: pubsub-task-queue
Found 4 workflow(s):
  - ConsumerA (from pubsub.domain_a.consumers)
  - ConsumerC (from pubsub.domain_a.consumers)
  - Dispatcher (from pubsub.common.dispatchers)
  - Producer (from pubsub.domain_a.producers)
Found 1 activity/activities:
  - DispatcherActivity (from pubsub.common.dispatchers)
Worker started on task queue: pubsub-task-queue
```

**Secondary Worker:**
```
Worker loading from packages: workflows=['pubsub.domain_b'], activities=['pubsub.domain_b']
Worker task queue: pubsub-task-queue-secondary
Found 1 workflow(s):
  - ConsumerB (from pubsub.domain_b.consumers)
Found 0 activity/activities:
Worker started on task queue: pubsub-task-queue-secondary
```

## Troubleshooting

### Consumer Not Receiving Events

1. Check if consumer is registered on correct worker:
   ```bash
   make logs worker | grep "Found.*workflow"
   ```

2. Verify task queue configuration in `@subscribe` decorator matches worker

3. Check Temporal UI for workflow execution errors

### Duplicate Workflows

Workflows are automatically deduplicated when loaded from multiple packages. The system uses `dict.fromkeys()` to maintain insertion order while removing duplicates.

### Worker Not Starting

1. Check Docker logs:
   ```bash
   make logs worker
   ```

2. Verify `.env` file has correct configuration

3. Ensure Temporal server is healthy:
   ```bash
   make logs temporal
   ```

## Key Features

- **Domain Isolation**: Separate domains with independent workers
- **Custom Task Queues**: Per-workflow task queue configuration
- **Automatic Discovery**: Dynamic workflow and activity discovery
- **Deduplication**: Automatic handling of duplicate workflow registrations
- **Hot Reload**: Watch mode for automatic worker restart on code changes
- **Module Path Logging**: Clear visibility of where components are loaded from
- **Flexible Architecture**: Easy to add new domains and workers
