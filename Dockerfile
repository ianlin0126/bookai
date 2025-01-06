FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-c", "import os; port = int(os.getenv('PORT', '8000')); os.system(f'python -m uvicorn app.main:app --host 0.0.0.0 --port {port}')"]
