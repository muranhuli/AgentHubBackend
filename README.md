# AgentHubBackend

For details on how to use these, please see [how_to_use.md](./how_to_use.md).

## Configuration

### Environment Files Setup

There are two types of environment configuration files:

1. **Middleware Environment** (`middleware/.env`): Docker deployment configuration for infrastructure services
2. **Runtime Environment** (`.env`): Agent runtime configuration including API keys and service endpoints

#### Setup Steps:

```bash
# Copy environment templates
cp .env.example .env
cp middleware/.env.example middleware/.env
```

Fill in your own parameters in the copied files according to your deployment needs.

### Middleware Configuration (Docker Services)

Configure infrastructure services in `middleware/.env`:

```
# Database and Cache
MYSQL_PORT=13306
MYSQL_ROOT_PASSWORD=<your-mysql-password>
REDIS_PORT=16379
REDIS_PASSWORD=<your-redis-password>

# Message Queue
RABBITMQ_PORT=15672
RABBITMQ_WEB_PORT=25672
RABBITMQ_USER=<your-rabbitmq-user>
RABBITMQ_PASSWORD=<your-rabbitmq-password>

# Object Storage
MINIO_API_PORT=19000
MINIO_CONSOLE_PORT=19001
MINIO_ROOT_USER=<your-minio-user>
MINIO_ROOT_PASSWORD=<your-minio-password>

# Vector Database
MILVUS_PORT=19530
MILVUS_MONITORING_PORT=19091
```

### Runtime Configuration (Agent Services)

Configure agent runtime parameters in `.env`:

```
# LLM API Keys
OPENAI_API_KEY=<your-openai-key>
ANTHROPIC_API_KEY=<your-anthropic-key>
AZURE_OPENAI_API_KEY=<your-azure-key>

# Custom LLM Service
SDU_API_KEY=<your-custom-llm-key>
SDU_BASE_URL=<your-custom-llm-endpoint>

# Embedding Service
EMBEDDING_URL=<your-embedding-endpoint>
EMBEDDING_API_KEY=<your-embedding-key>
EMBEDDING_MODEL=<your-embedding-model>
```

Minio operators are available for writing, reading and deleting objects.