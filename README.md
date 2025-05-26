# Service - Cyberpartner Create

A microservice that generates and manages cyberpartners for CKC25. 
This service consumes Kafka messages, creates new cyberpartners based on badge IDs, and stores them in Redis. 
It's built with Python 3.12 and uses Poetry for dependency management.

## Key Features
- Consumes messages from the Kafka topic: ``ingress-cackalacky-cyberpartner-create`` to trigger cyberpartner creation
- Generates unique cyberpartner entities with randomized attributes
- Stores cyberpartner data in Redis
- Produces messages to downstream services via Kafka
- Containerized with Docker for easy deployment

## Tech Stack
- Python 3.12
- Poetry for dependency management
- Kafka for message processing
- Redis for data storage
- Docker and Docker Compose for containerization
- CircleCI for CI/CD pipeline
- ArgoCD for Kubernetes deployment

## Build

### Pre-req windows

py3.12
poetry
```bash
pipx install poetry
poetry --version
```

https://scoop.sh/
https://pipx.pypa.io/stable/installation/

# Local Run - Docker

Docker compose w/doppler to inject secrets / os vars

```bash
# Build the image
doppler run -- docker compose -f docker-compose.services.yaml build

# Run with infrastructure (Kafka, Redis, etc.)
doppler run -- docker compose -f docker-compose.infrastructure.yaml up -d
doppler run -- docker compose -f docker-compose.services.yaml up -d
```

# Maintenance

```bash
poetry run isort .
poetry run black .
```

# TODO
 - taskfile
 - docker commands for local