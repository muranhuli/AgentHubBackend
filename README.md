# AgentHubBackend

## Configuration

### Environment Files Setup

1. Copy the template files and configure your parameters:

```bash
# Copy environment templates
cp .env-template .env
cp .env-llm-template .env-llm
```

2. Fill in your own parameters in the copied files.

### Minio Configuration

The runtime relies on a Minio service for object storage. Set the following variables in `middleware/.env`:

```
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ROOT_USER=<your-access-key>
MINIO_ROOT_PASSWORD=<your-secret-key>
```

### LLM Configuration

Configure your LLM API keys in `.env-llm` file after copying from the template.

Minio operators are available for writing, reading and deleting objects.