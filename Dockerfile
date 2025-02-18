FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a script to run migrations and start the app
RUN echo '#!/bin/sh\n\
alembic upgrade head\n\
python -c "import os; port = int(os.getenv(\'PORT\', \'8000\')); os.system(f\'python -m uvicorn app.main:app --host 0.0.0.0 --port {port}\')"' > /app/start.sh \
    && chmod +x /app/start.sh

CMD ["/app/start.sh"]
