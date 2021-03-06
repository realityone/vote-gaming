all:
	$(MAKE) -C result release
	$(MAKE) -C vote release
	$(MAKE) -C database release
	$(MAKE) -C entrypoint release
	$(MAKE) -C worker release
	$(MAKE) -C ui release

image:
	docker pull daocloud.io/alphabeta_com/vg-result
	docker pull daocloud.io/alphabeta_com/vg-vote
	docker pull daocloud.io/alphabeta_com/vg-database
	docker pull daocloud.io/alphabeta_com/vg-entrypoint
	docker pull daocloud.io/alphabeta_com/vg-mqueue
	docker pull daocloud.io/alphabeta_com/vg-worker
	docker pull daocloud.io/alphabeta_com/vg-ui

up-backend:
	sed "s/__HOSTIP__/$(HOSTIP)/g" backend.tmpl.yml > backend.yml
	docker-compose -f backend.yml up -d

up-entrypoint:
	sed "s/__HOSTIP__/$(HOSTIP)/g; s/__ENTRYPOINT__/$(ENTRYPOINT)/g;" entrypoint.tmpl.yml > entrypoint.yml
	docker-compose -f entrypoint.yml up -d

up-frontend:
	sed "s/__ENTRYPOINT__/$(ENTRYPOINT)/g" frontend.tmpl.yml > frontend.yml
	docker-compose -f frontend.yml up -d

up: up-backend up-entrypoint up-frontend

.PHONY: all