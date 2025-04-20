# Cyberpartner Event Ingress Highway

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

### Configure Private PyPI Repository

#### Method 1: Poetry Config (Recommended)
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

### Local Run - Docker

Docker compose w/doppler to inject secrets / os vars

```bash
doppler run -- docker compose up -d
```

# Maintenance

```bash
poetry run isort src
poetry run black src
```

# TODO
 - taskfile
 - docker commands for local