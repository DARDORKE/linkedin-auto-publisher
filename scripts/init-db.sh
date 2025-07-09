#!/bin/bash

# Create necessary directories
echo "Creating directories..."
mkdir -p /app/data /app/logs

# Initialize database
echo "Initializing database..."
python -c "
from src.database import DatabaseManager
db = DatabaseManager()
print('Database initialized successfully!')
"

echo "Database initialization complete!"