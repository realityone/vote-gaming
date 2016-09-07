database:
	docker pull daocloud.io/mysql
	docker tag daocloud.io/mysql daocloud.io/realityone/vg-database

release: database
	docker push daocloud.io/realityone/vg-database
