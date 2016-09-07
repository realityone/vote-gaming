all:
	$(MAKE) -C result release
	$(MAKE) -C vote release
	$(MAKE) -C database release
	$(MAKE) -C entrypoint release

image:
	docker pull daocloud.io/realityone/vg-result
	docker pull daocloud.io/realityone/vg-vote
	docker pull daocloud.io/realityone/vg-database
	docker pull daocloud.io/realityone/vg-entrypoint
	docker pull daocloud.io/realityone/vg-mqueue

.PHONY: all