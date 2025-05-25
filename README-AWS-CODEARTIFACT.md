# Service - Cyberpartner Create

A microservice that generates and manages cyberpartner entities for the Cackalacky platform. 
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

# AWS CodeArtifact

Adding for private dev on subsequent iterations.

### Configure Private PyPI Repository (CodeArtifact)

#### Method 1: Poetry Config
```bash
# Configure the repository URL (note the /simple/ at the end)
poetry config repositories.lockfale https://lockfale-059039070213.d.codeartifact.us-east-1.amazonaws.com/pypi/lockfale/simple/

# Set authentication (replace TOKEN with your CodeArtifact token)
poetry config http-basic.lockfale aws TOKEN
```

#### Method 2: Environment Variables
Windows (PowerShell):
```powershell
$env:POETRY_HTTP_BASIC_LOCKFALE_USERNAME="aws"
$env:POETRY_HTTP_BASIC_LOCKFALE_PASSWORD="YOUR_CODEARTIFACT_TOKEN"
```

Mac/Linux:
```bash
export POETRY_HTTP_BASIC_LOCKFALE_USERNAME="aws"
export POETRY_HTTP_BASIC_LOCKFALE_PASSWORD="YOUR_CODEARTIFACT_TOKEN"
```

To get your CodeArtifact token:
```bash
# AWS CLI v2
aws codeartifact get-authorization-token --domain lockfale --domain-owner 059039070213 --query authorizationToken --output text
```

# Local Run - Docker

Docker compose w/doppler to inject secrets / os vars

```bash
# First get the token
export CODEARTIFACT_TOKEN=$(aws codeartifact get-authorization-token --domain ... --domain-owner ... --query authorizationToken --output text)

# Build the image
doppler run -- docker compose -f docker-compose.services.yaml build --build-arg CODEARTIFACT_TOKEN=$env:CODEARTIFACT_TOKEN

# Run with infrastructure (Kafka, Redis, etc.)
doppler run -- docker compose -f docker-compose.infrastructure.yaml up -d
doppler run -- docker compose -f docker-compose.services.yaml up -d
```

# Maintenance

```bash
poetry run isort src
poetry run black src
```

# TODO
 - taskfile
 - docker commands for local