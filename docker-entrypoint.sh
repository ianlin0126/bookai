#!/bin/sh
alembic upgrade head
python -c "import os; port = int(os.getenv('PORT', '8000')); os.system(f'python -m uvicorn app.main:app --host 0.0.0.0 --port {port}')"
