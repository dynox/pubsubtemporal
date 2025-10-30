SHELL := /bin/zsh

COMPOSE := docker compose

.PHONY: help up down restart logs worker worker-logs worker-restart ps watch watch-worker wf-producer wf-producer-activity wf-producer-workflow

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
	@echo "  wf-producer             - Start ProducerWorkflow (no parameters) via Temporal CLI"
	@echo "  wf-producer-activity    - Start ProducerActivityWorkflow with EVENT_TYPE arg"
	@echo "  wf-producer-workflow    - Start ProducerWorkflowWorkflow with EVENT_TYPE arg"

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
	$(COMPOSE) up --watch

wf-producer:
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type ProducerWorkflow \
	  --workflow-id producer-$$RANDOM \
	  --input "{\"name\":null}"

wf-producer-activity:
	@if [ -z "$(EVENT_TYPE)" ]; then \
		echo "Error: EVENT_TYPE is required. Usage: make wf-producer-activity EVENT_TYPE=event.a"; \
		exit 1; \
	fi
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type ProducerActivityWorkflow \
	  --workflow-id producer-activity-$(EVENT_TYPE)-$$RANDOM \
	  --input "{\"event_type\":\"$(EVENT_TYPE)\",\"payload\":null}"

wf-producer-workflow:
	@if [ -z "$(EVENT_TYPE)" ]; then \
		echo "Error: EVENT_TYPE is required. Usage: make wf-producer-workflow EVENT_TYPE=event.a"; \
		exit 1; \
	fi
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type ProducerWorkflowWorkflow \
	  --workflow-id producer-workflow-$(EVENT_TYPE)-$$RANDOM \
	  --input "{\"event_type\":\"$(EVENT_TYPE)\",\"payload\":null}"

