release: alembic upgrade head
web: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT