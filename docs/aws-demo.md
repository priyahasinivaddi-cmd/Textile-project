# AWS EC2 demo deployment

This deployment runs the frontend, API, worker, PostgreSQL, and Redis on one EC2 instance. It is intended for a demonstration, not a highly available production system.

## 1. Create the server

In AWS, launch an Ubuntu 24.04 LTS EC2 instance in `ap-south-1` (Mumbai).

- Instance size: `t3.large` recommended for the API, worker, and ML dependencies. `t3.medium` may work if model memory use is modest.
- Storage: at least 30 GB gp3.
- Security group inbound rules:
  - SSH (TCP 22) from **My IP** only.
  - HTTP (TCP 80) from `0.0.0.0/0`.
- Do not open ports 5432, 6379, 8000, or 5173.

Allocate and associate an Elastic IP if the demo URL must remain unchanged after the instance is stopped.

## 2. Install Docker

Connect to the instance and install Docker Engine and the Docker Compose plugin using Docker's official Ubuntu installation instructions. Confirm both commands work:

```sh
docker --version
docker compose version
```

## 3. Transfer the project

Clone the repository on the instance, or copy the `textile-project` directory to it. Then enter the project directory.

Create the private environment file:

```sh
cp .env.aws-demo.example .env.aws-demo
nano .env.aws-demo
```

Replace all placeholder values. Set `PUBLIC_ORIGIN` to `http://` followed by the instance's public or Elastic IP, without a trailing slash. Generate independent random values for `POSTGRES_PASSWORD` and `SECRET_KEY`; the secret key must be at least 32 characters.

## 4. Start the application

```sh
docker compose --env-file .env.aws-demo -f docker-compose.aws-demo.yml up -d --build
docker compose --env-file .env.aws-demo -f docker-compose.aws-demo.yml ps
```

The first build can take several minutes because Python and ML dependencies are installed. Open `http://YOUR_EC2_PUBLIC_IP` when all containers are healthy.

Verify the API through the same public endpoint:

```sh
curl http://YOUR_EC2_PUBLIC_IP/health
curl http://YOUR_EC2_PUBLIC_IP/health/db
curl http://YOUR_EC2_PUBLIC_IP/health/ml
```

The ML endpoint may report `degraded` when trained artifacts are not present; the rest of the demo can still run with the application's fallback behavior.

## Updating and troubleshooting

After pulling or copying new code, rebuild and restart:

```sh
docker compose --env-file .env.aws-demo -f docker-compose.aws-demo.yml up -d --build
```

View recent logs:

```sh
docker compose --env-file .env.aws-demo -f docker-compose.aws-demo.yml logs --tail=100
```

Stop the demo without deleting its database or uploads:

```sh
docker compose --env-file .env.aws-demo -f docker-compose.aws-demo.yml down
```

Stopping or terminating AWS resources may incur data loss. Avoid `down --volumes` unless the demo data can be discarded.
