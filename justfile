set dotenv-load := true

[private]
default:
    @just --list

# Export database to backup file
backup:
    pg_dump -U postgres -h $PGHOST_PROD -p $PGPORT_PROD -W -f backups/database-{{datetime("%F")}}.bak -F t railway

psql:
    psql -U postgres -h $PGHOST_PROD -p $PGPORT_PROD -t railway

# Generate new migrations based on model changes
makemigrations:
    uv run manage.py makemigrations

# Apply database migrations
migrate:
    uv run manage.py migrate

# Run server in development mode
run:
    uv run manage.py runserver 0.0.0.0:8888

# Run server in production mode
run-prod:
    docker/entrypoint.sh

# Seed database with dummy data
seed: migrate
    uv run manage.py seed

# Run tests
test *arguments="":
    uv run pytest {{arguments}}

# Run behavioral tests
behave arguments="":
    uv run manage.py behave {{arguments}}
