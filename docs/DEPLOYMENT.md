# Deployment

Local:

```bash
cp .env.example .env
docker compose up --build
```

Production:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

Run migrations with Alembic before switching real traffic:

```bash
cd backend
alembic -c app/db/alembic.ini upgrade head
```

Services:

- `api`: FastAPI app on port 8000.
- `worker`: scheduler/polling worker.
- `postgres`: primary database.
- `redis`: locks/cache/worker coordination.

Health checks:

- `GET /health`
- `GET /ready`
