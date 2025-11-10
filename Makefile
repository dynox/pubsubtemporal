SHELL := /bin/zsh

COMPOSE := docker compose

.PHONY: help up down restart logs watch wf-producer-activity wf-producer-activity-repeated wf-producer-signal wf-registry-logger wf-search-producer register-search-attr

help:
	@echo "Available targets:"
	@echo "  up              - Build and start full Temporal stack (DB, server, UI, tools, worker)"
	@echo "  down            - Stop and remove all services"
	@echo "  restart         - Restart all services"
	@echo "  logs [SERVICE...] - Tail all services logs (or specific service(s) if provided)"
	@echo "  watch                   - Start full stack with compose watch"
	@echo "  wf-producer          - Start Producer workflow with EVENT_TYPE arg"
	@echo "  wf-search-producer   - Start SearchProducer workflow with EVENT_TYPE arg (uses SearchAttributes)"
	@echo "  register-search-attr - Register 'subscribed_on' search attribute (one-time setup)"

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

%:
	@:

watch:
	$(COMPOSE) up --build --watch

wf-producer:
	@if [ -z "$(EVENT_TYPE)" ]; then \
		echo "Error: EVENT_TYPE is required. Usage: make wf-producer EVENT_TYPE=event.a"; \
		exit 1; \
	fi
	@EVENT_ID=$$(python3 -c "import uuid; print(uuid.uuid4())"); \
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type Producer \
	  --workflow-id producer-activity-$(EVENT_TYPE)-$$RANDOM \
	  --input "{\"id\":\"$$EVENT_ID\",\"event_type\":\"$(EVENT_TYPE)\",\"payload\":null}"

wf-registry-logger:
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type RegistryLoggerWorkflow \
	  --workflow-id registry-logger-$$RANDOM 

wf-search-producer:
	@if [ -z "$(EVENT_TYPE)" ]; then \
		echo "Error: EVENT_TYPE is required. Usage: make wf-search-producer EVENT_TYPE=event.a"; \
		exit 1; \
	fi
	@EVENT_ID=$$(python3 -c "import uuid; print(uuid.uuid4())"); \
	$(COMPOSE) exec temporal-admin-tools temporal workflow start \
	  --tls=false --namespace default --task-queue pubsub-task-queue \
	  --type SearchProducer \
	  --workflow-id search-producer-$(EVENT_TYPE)-$$RANDOM \
	  --input "{\"id\":\"$$EVENT_ID\",\"event_type\":\"$(EVENT_TYPE)\",\"payload\":null}"

register-search-attr:
	@echo "Registering 'subscribed_on' search attribute..."
	$(COMPOSE) exec temporal-admin-tools temporal operator search-attribute create \
	  --namespace default --name subscribed_on --type Keyword || \
	  echo "Search attribute may already exist (this is OK)"

