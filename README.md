# AgentHubBackend
\nThis project uses a new LLM operator for LLM calls. Configure API keys in `.env-llm`.

The runtime relies on a Minio service for object storage. Set the following variables in `middleware/.env`:

```
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
MINIO_ROOT_USER=<your-access-key>
MINIO_ROOT_PASSWORD=<your-secret-key>
```

Minio operators are available for writing, reading and deleting objects.
