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

up:
	sed "s/__HOSTIP__/$(HOSTIP)" database.tmpl.yml > database.yml
	sed "s/__HOSTIP__/$(HOSTIP)" entrypoint.tmpl.yml > entrypoint.yml
	docker-compose -f database.yml up -d
	docker-compose -f entrypoint.yml up -d

.PHONY: all