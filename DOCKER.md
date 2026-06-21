# Docker Setup
This project runs as three containers:

- `frontend`: React app built by Vite and served by Nginx.
- `backend`: FastAPI app served by Uvicorn.
- `db`: Postgres database for optimization sessions and prompt versions.

## Run Locally


Create a local `.env` from the example and set your real API key (GROQ):

```env
GROQ_API_KEY=your-groq-api-key
API_AUTH_TOKEN=change-this-dev-token
```

Then run:

```bash
docker compose up --build
```

Open:

```text
http://localhost:5173
```

The backend is available at:

```text
http://localhost:8000
```

## Useful Commands

```bash
docker compose down
docker compose down -v
docker compose logs backend
docker compose logs frontend
```

Use `docker compose down -v` when you want to delete the local Postgres volume and start with a fresh database.

Troubleshooting: if the backend fails to start, check `docker compose logs backend` for stack traces and ensure the `.env` values are set.

Note: the backend's judge agent now adapts scoring criteria based on `task_type`.
If you rely on a fixed set of scores, update integrations to handle dynamic `scores` keys.
