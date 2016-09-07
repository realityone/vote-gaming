database:
	docker pull daocloud.io/mysql
	docker pull daocloud.io/daocloud/dce-etcd:1.4.0
	docker tag daocloud.io/mysql daocloud.io/realityone/vg-database
	docker tag daocloud.io/daocloud/dce-etcd:1.4.0 daocloud.io/realityone/vg-mqueue

release: database
	docker push daocloud.io/realityone/vg-database
	docker push daocloud.io/realityone/vg-mqueue
