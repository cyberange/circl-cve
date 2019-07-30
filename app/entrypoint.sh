#!/usr/bin/env bash
WORKERS=${WORKERS:-1}
ACCESS_LOG=${ACCESS_LOG:--}
ERROR_LOG=${ERROR_LOG:--}

if [ -z "$SECRET_KEY" ]; then
    echo "[ ERROR ] You must define the SECRET_KEY environment variable"
    echo "[ ERROR ] Exiting..."
    exit 1
fi

# Check that the database is available
database=`echo $DB_HOST`
port=`echo $DB_PORT`
echo "Waiting for $database:$port to be ready"
while ! mysqladmin ping -h "$database" -P "$port" --silent; do
    # Show some progress
    echo -n '.';
    sleep 1;
done
echo "$database is ready"
# Give it another second.
sleep 1;

python create.py
echo "Starting CIRCL-CVE"

exec gunicorn 'server:app' \
    --bind '0.0.0.0:8000' \
    --workers $WORKERS \
    --access-logfile "$ACCESS_LOG" \
    --error-logfile "$ERROR_LOG"
