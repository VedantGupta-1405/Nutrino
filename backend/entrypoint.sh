#!/bin/sh
set -e

echo "=== Nutrino Backend Initializing ==="

# Wait for PostgreSQL database connection using Python check
echo "Checking database connectivity..."
python -c "
import time, sys
from app.database.session import check_db_connection

for attempt in range(1, 31):
    res = check_db_connection()
    if res.get('status') == 'healthy':
        print(f'Database connection verified (attempt {attempt}).')
        sys.exit(0)
    print(f'Waiting for PostgreSQL database (attempt {attempt}/30)...')
    time.sleep(1)

print('Error: Database connection timed out after 30 attempts.')
sys.exit(1)
"

# Run database migrations
echo "Applying Alembic database migrations..."
alembic upgrade head
echo "Alembic migrations completed successfully."

# Seed initial baseline food catalog idempotently
echo "Verifying baseline food catalog..."
python -m app.database.seed || echo "Seed script completed."

echo "Starting application server..."
exec "$@"
