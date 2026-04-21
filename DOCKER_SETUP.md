# Docker Setup Guide 🐳

## Services Overview

Your `docker-compose.yml` now includes **4 services**:

### 1. **Redis** 🔴
- **Image**: `redis:7-alpine`
- **Port**: `6379`
- **Purpose**: Cache for chat history (20-100x faster than MongoDB)
- **Storage**: Persistent volume (`redis_data`)
- **Health Check**: `redis-cli ping`

### 2. **Qdrant** 🔵
- **Image**: `qdrant/qdrant:latest`
- **Ports**: `6333` (HTTP API), `6334` (gRPC)
- **Purpose**: Vector database for embeddings (alternative to FAISS)
- **Storage**: Persistent volume (`qdrant_storage`)
- **Health Check**: HTTP health endpoint

### 3. **Backend** 🟢
- **Build**: From `Dockerfile`
- **Port**: `5000` → `10000` (internal)
- **Purpose**: FastAPI application
- **Dependencies**: Waits for Redis and Qdrant to be healthy
- **Volumes**: 
  - `./vector_store_data:/app/vector_store_data` (FAISS persistence)

### 4. **Frontend** 🟡
- **Build**: From `frontend/Dockerfile`
- **Port**: `3000`
- **Purpose**: React/Vite application
- **Dependencies**: Waits for backend

---

## Quick Start

### 1. **Start All Services**
```bash
docker-compose up -d
```

### 2. **View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f redis
docker-compose logs -f qdrant
```

### 3. **Check Status**
```bash
docker-compose ps
```

### 4. **Stop All Services**
```bash
docker-compose down
```

### 5. **Stop and Remove Volumes** (⚠️ Deletes all data)
```bash
docker-compose down -v
```

---

## Configuration Options

### Option 1: Local Docker (Default) ✅

**Best for**: Development, testing, local deployment

**Configuration** (`.env`):
```env
# Redis - Local Docker
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_USERNAME=default

# Qdrant - Local Docker (optional)
USE_QDRANT=false
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=
```

**Pros**:
- ✅ Free
- ✅ No internet required
- ✅ Fast local access
- ✅ Full control

**Cons**:
- ❌ Data only on your machine
- ❌ Requires Docker resources

---

### Option 2: Cloud Services

**Best for**: Production, team collaboration, scalability

**Configuration** (`.env`):
```env
# Redis Cloud
REDIS_HOST=redis-17413.crce182.ap-south-1-1.ec2.cloud.redislabs.com
REDIS_PASSWORD=RqEhFitk4zDZ25aaZWS1epGR9jwoB2JB
REDIS_PORT=17413
REDIS_USERNAME=default

# Qdrant Cloud
USE_QDRANT=true
QDRANT_URL=https://66a1074e-7628-4d8b-8b54-42e698522acb.us-east-1-1.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Pros**:
- ✅ Accessible from anywhere
- ✅ Managed backups
- ✅ Better scalability
- ✅ No local resources needed

**Cons**:
- ❌ Costs money
- ❌ Requires internet
- ❌ Potential latency

---

## Vector Store Options

### FAISS (Default) 📦

**Configuration**:
```env
USE_QDRANT=false
```

**Storage**: `./vector_store_data/`
- `faiss.index` - Vector index
- `chunks.pkl` - Metadata

**Pros**:
- ✅ Simple setup
- ✅ No external dependencies
- ✅ Fast for small datasets

**Cons**:
- ❌ Limited scalability
- ❌ No advanced filtering
- ❌ Requires rebuilding for deletions

---

### Qdrant 🚀

**Configuration**:
```env
USE_QDRANT=true
QDRANT_URL=http://qdrant:6333  # or cloud URL
```

**Storage**: Docker volume or cloud

**Pros**:
- ✅ Better scalability
- ✅ Advanced filtering
- ✅ Efficient deletions
- ✅ Built-in persistence
- ✅ REST API

**Cons**:
- ❌ More complex setup
- ❌ Requires additional service

---

## Service URLs

When running locally:

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web UI |
| Backend API | http://localhost:5000/api/v1 | REST API |
| Backend Docs | http://localhost:5000/docs | Swagger UI |
| Redis | localhost:6379 | Cache |
| Qdrant UI | http://localhost:6333/dashboard | Vector DB UI |
| Qdrant API | http://localhost:6333 | Vector DB API |

---

## Persistent Data

### Docker Volumes (Managed by Docker)
```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect pdf-chatbot_redis_data
docker volume inspect pdf-chatbot_qdrant_storage

# Remove volumes (⚠️ deletes data)
docker volume rm pdf-chatbot_redis_data
docker volume rm pdf-chatbot_qdrant_storage
```

### Host Directories (Visible on your machine)
```
./vector_store_data/    # FAISS index (if USE_QDRANT=false)
  ├── faiss.index
  └── chunks.pkl
```

---

## Troubleshooting

### Redis Connection Issues
```bash
# Check Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG

# View Redis logs
docker-compose logs redis
```

### Qdrant Connection Issues
```bash
# Check Qdrant is running
docker-compose ps qdrant

# Test Qdrant health
curl http://localhost:6333/health

# View Qdrant logs
docker-compose logs qdrant

# Access Qdrant UI
open http://localhost:6333/dashboard
```

### Backend Not Starting
```bash
# Check dependencies are healthy
docker-compose ps

# View backend logs
docker-compose logs backend

# Restart backend only
docker-compose restart backend
```

### Port Conflicts
If ports are already in use:

**Edit `docker-compose.yml`**:
```yaml
services:
  redis:
    ports:
      - "6380:6379"  # Change 6379 to 6380
  
  qdrant:
    ports:
      - "6335:6333"  # Change 6333 to 6335
```

---

## Development Workflow

### 1. **First Time Setup**
```bash
# Start all services
docker-compose up -d

# Watch logs
docker-compose logs -f backend
```

### 2. **Code Changes**
```bash
# Rebuild and restart backend
docker-compose up -d --build backend

# Or restart without rebuild
docker-compose restart backend
```

### 3. **Database Reset**
```bash
# Stop services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

### 4. **Clean Rebuild**
```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker-compose rm -f

# Rebuild from scratch
docker-compose build --no-cache

# Start
docker-compose up -d
```

---

## Production Deployment

### Recommended Configuration

1. **Use Cloud Services**:
   - Redis Cloud for caching
   - Qdrant Cloud for vectors
   - MongoDB Atlas for database

2. **Update `.env`**:
   ```env
   USE_QDRANT=true
   REDIS_HOST=<your-redis-cloud-host>
   QDRANT_URL=<your-qdrant-cloud-url>
   ```

3. **Remove Local Services** from `docker-compose.yml`:
   - Comment out `redis` service
   - Comment out `qdrant` service
   - Keep only `backend` and `frontend`

4. **Deploy**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

---

## Resource Usage

Typical resource consumption:

| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| Redis | ~1% | ~10 MB | ~50 MB |
| Qdrant | ~2% | ~100 MB | ~500 MB |
| Backend | ~5% | ~200 MB | ~1 GB |
| Frontend | ~1% | ~50 MB | ~100 MB |

**Total**: ~300-400 MB RAM, ~2 GB disk

---

## Next Steps

1. ✅ Start services: `docker-compose up -d`
2. ✅ Check logs: `docker-compose logs -f`
3. ✅ Open frontend: http://localhost:3000
4. ✅ Upload a PDF and test
5. ✅ Check Redis cache is working (logs will show "REDIS CONNECTED")
6. ✅ (Optional) Enable Qdrant: Set `USE_QDRANT=true` in `.env`

---

## Support

- **Docker Docs**: https://docs.docker.com/compose/
- **Redis Docs**: https://redis.io/docs/
- **Qdrant Docs**: https://qdrant.tech/documentation/
