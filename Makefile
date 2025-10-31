SHELL := /bin/zsh

COMPOSE := docker compose

.PHONY: help up down restart logs worker worker-logs worker-restart ps watch watch-worker wf-producer-activity wf-producer-activity-repeated wf-producer-workflow wf-producer-signal wf-registry-logger

help:
	@echo "Available targets:"
	@echo "  up              - Build and start full Temporal stack (DB, server, UI, tools, worker)"
	@echo "  down            - Stop and remove all services"
	@echo "  restart         - Restart all services"
	@echo "  logs [SERVICE...] - Tail all services logs (or specific service(s) if provided)"
	@echo "  worker          - Build and start only the worker"
	@echo "  worker-restart  - Restart worker"
	@echo "  ps                      - Show compose services status"
	@echo "  watch                   - Start full stack with compose watch"
	@echo "  wf-producer-activity          - Start ProducerActivity with EVENT_TYPE arg"
	@echo "  wf-producer-activity-repeated - Start ProducerActivityRepeated with EVENT_TYPE arg"
	@echo "  wf-producer-workflow          - Start ProducerWorkflow with EVENT_TYPE arg"
	@echo "  wf-producer-signal            - Start ProducerSignal with EVENT_TYPE arg"
	@echo "  wf-registry-logger            - Start RegistryLoggerWorkflow to log all workflows and activities"

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) up -d --build 

logs:
	@SERVICES="$(filter-out $@,$(MAKECMDGOALS))"; \
	if [ -z "$$SERVICES" ]; then \
		$(COMPOSE) logs -f; \
	else \
		$(COMPOSE) logs -f $$SERVICES; \
	fi

worker:
	@if [ -z "$(filter logs,$(MAKECMDGOALS))" ]; then \
		$(COMPOSE) up -d --build worker; \
	fi

%:
	@:

worker-restart:
	$(COMPOSE) rm -sf worker || true
	$(COMPOSE) up -d --build worker

ps:
	$(COMPOSE) ps

watch:
	$(COMPOSE) up --build --watch

wf-producer-activity:
	@if [ -z "$(EVENT_TYPE)" ]; then \
		echo "Error: EVENT_TYPE is required. Usage: make wf-producer-activity EVENT_TYPE=event.a"; \
		exit 1; \
	fi
	@EVENT_ID=$$(python3 -c "import uuid; print(uuid.uuid4())"); \
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type ProducerActivity \
	  --workflow-id producer-activity-$(EVENT_TYPE)-$$RANDOM \
	  --input "{\"id\":\"$$EVENT_ID\",\"event_type\":\"$(EVENT_TYPE)\",\"payload\":null}"

wf-producer-activity-repeated:
	@if [ -z "$(EVENT_TYPE)" ]; then \
		echo "Error: EVENT_TYPE is required. Usage: make wf-producer-activity-repeated EVENT_TYPE=event.a"; \
		exit 1; \
	fi
	@EVENT_ID=$$(python3 -c "import uuid; print(uuid.uuid4())"); \
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type ProducerActivityRepeated \
	  --workflow-id producer-activity-repeated-$(EVENT_TYPE)-$$RANDOM \
	  --input "{\"id\":\"$$EVENT_ID\",\"event_type\":\"$(EVENT_TYPE)\",\"payload\":null}"

wf-producer-workflow:
	@if [ -z "$(EVENT_TYPE)" ]; then \
		echo "Error: EVENT_TYPE is required. Usage: make wf-producer-workflow EVENT_TYPE=event.a"; \
		exit 1; \
	fi
	@EVENT_ID=$$(python3 -c "import uuid; print(uuid.uuid4())"); \
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type ProducerWorkflow \
	  --workflow-id producer-workflow-$(EVENT_TYPE)-$$RANDOM \
	  --input "{\"id\":\"$$EVENT_ID\",\"event_type\":\"$(EVENT_TYPE)\",\"payload\":null}"

wf-producer-signal:
	@if [ -z "$(EVENT_TYPE)" ]; then \
		echo "Error: EVENT_TYPE is required. Usage: make wf-producer-signal EVENT_TYPE=event.a"; \
		exit 1; \
	fi
	@EVENT_ID=$$(python3 -c "import uuid; print(uuid.uuid4())"); \
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type ProducerSignal \
	  --workflow-id producer-signal-$(EVENT_TYPE)-$$RANDOM \
	  --input "{\"id\":\"$$EVENT_ID\",\"event_type\":\"$(EVENT_TYPE)\",\"payload\":null}"

wf-registry-logger:
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type RegistryLoggerWorkflow \
	  --workflow-id registry-logger-$$RANDOM 

