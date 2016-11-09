database:
	docker pull daocloud.io/mysql
	docker pull daocloud.io/daocloud/dce-etcd:1.4.0
	docker tag daocloud.io/mysql daocloud.io/alphabeta_com/vg-database
	docker tag daocloud.io/daocloud/dce-etcd:1.4.0 daocloud.io/alphabeta_com/vg-mqueue

release: database
	docker push daocloud.io/alphabeta_com/vg-database
	docker push daocloud.io/alphabeta_com/vg-mqueue
