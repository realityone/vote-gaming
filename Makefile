all:
	$(MAKE) -C result release
	$(MAKE) -C vote release
	$(MAKE) -C database release
	$(MAKE) -C entrypoint release
	$(MAKE) -C worker release

image:
	docker pull daocloud.io/realityone/vg-result
	docker pull daocloud.io/realityone/vg-vote
	docker pull daocloud.io/realityone/vg-database
	docker pull daocloud.io/realityone/vg-entrypoint
	docker pull daocloud.io/realityone/vg-mqueue
	docker pull daocloud.io/realityone/vg-worker

up-backend:
	sed "s/__HOSTIP__/$(HOSTIP)/g" backend.tmpl.yml > backend.yml
	docker-compose -f backend.yml up -d

up-entrypoint:
	sed "s/__HOSTIP__/$(HOSTIP)/g" entrypoint.tmpl.yml > entrypoint.yml
	docker-compose -f entrypoint.yml up -d

up: up-backend up-entrypoint

.PHONY: all