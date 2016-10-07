# vote-gaming

> Serverless like application inspired from https://github.com/bfirsh/serverless-docker-voting-app.

This is a serverless like application with Docker and developed in 2016 Beijing AWS Hackathon.

## Architecture

- **vg-entrypoint**: Work like an reverse proxy, accept all requests and dispatch to several backend applications, then response it.

+ Backend
  - **vg-mqueue**: Actually is an ETCD(cluster), use watch api to notice worker which container should be unpause.
  - **vg-worker**: Only pause and unpause container.
  - **vg-database**: Just a MySQL.

+ Frontend
  - **vg-result**: The Voting result API.
  - **vg-vote**: The Vote API.
  - **vg-ui**: The voting result display layer use Ajax request to vote or result.

## Improvement

Docker provide a demo to show serverless application by run container and remove container on demand. But this will cause Docker Daemon use large CPU and it always hangs under heavy load.

This demo use pause/unpause to avoid create/remove container.

When **vg-entrypoint** accept a request from user, it will be dispatched to **vg-result** or **vg-vote**, and response the request.