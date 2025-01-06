web: python -c "
import os
import pathlib

# Create data directory if it doesn't exist
data_dir = pathlib.Path('/data')
data_dir.mkdir(exist_ok=True)

# Set environment variables
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///data/bookai.db')

# Get port
port = int(os.getenv('PORT', '8000'))

# Start the application
os.system(f'python -m uvicorn app.main:app --host 0.0.0.0 --port {port}')
"
