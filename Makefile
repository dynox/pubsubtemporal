SHELL := /bin/zsh

COMPOSE := docker compose

.PHONY: help up down restart logs worker worker-logs worker-restart ps watch watch-worker wf-producer

help:
	@echo "Available targets:"
	@echo "  up              - Build and start full Temporal stack (DB, server, UI, tools, worker)"
	@echo "  down            - Stop and remove all services"
	@echo "  restart         - Restart all services"
	@echo "  logs [SERVICE...] - Tail all services logs (or specific service(s) if provided)"
	@echo "  worker          - Build and start only the worker"
	@echo "  worker-restart  - Restart worker"
	@echo "  ps              - Show compose services status"
	@echo "  watch           - Start full stack with compose watch"
	@echo "  wf-producer     - Start ProducerWorkflow (no parameters) via tctl"

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
	$(COMPOSE) exec temporal-admin-tools tctl --ns default workflow start \
	  --taskqueue pubsub-task-queue --workflow_type ProducerWorkflow --workflow_id producer-$$RANDOM

