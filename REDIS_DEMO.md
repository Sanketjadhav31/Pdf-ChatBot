# Redis Cache Demo

## How to See Redis in Action

### Step 1: Start the Server
```bash
uvicorn main:app --port 5000
```

Look for these logs on startup:
```
================================================================================
🔌 REDIS CONNECTION
================================================================================
Host: redis-17413.crce182.ap-south-1-1.ec2.cloud.redislabs.com
Port: 17413
Max Messages: 6
TTL: 24 hours
✅ REDIS CONNECTED - Cache is active
⚡ Chat history will load 20-100x faster!
================================================================================
```

### Step 2: Run the Demo Script
```bash
python demo_redis.py
```

### Step 3: Watch the Server Terminal

You'll see these Redis operations:

#### First Message (Cache Miss)
```
🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍
📦 REDIS CACHE CHECK
🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍
Session: abc123-session-id
User: redis_test
❌ REDIS CACHE MISS - Loading from MongoDB
⏱️  Performance: ~50-100ms (Slower)
✅ REDIS CACHE POPULATED - Stored 0 messages for next time
================================================================================
```

#### After Response (Cache Update)
```
💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾
📝 REDIS CACHE UPDATE
💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾💾
✅ REDIS CACHE UPDATED - Added 2 new messages
⚡ Next request will be faster (cache hit)
================================================================================
```

#### Second Message (Cache Hit - Fast!)
```
🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍
📦 REDIS CACHE CHECK
🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍🔍
Session: abc123-session-id
User: redis_test
✅ REDIS CACHE HIT - Using 2 messages from Redis
⚡ Performance: ~1-5ms (Fast!)
================================================================================
```

## What to Look For

### Redis is Working When You See:
- ✅ `REDIS CONNECTED - Cache is active` on startup
- ✅ `REDIS CACHE HIT` on subsequent messages
- ✅ `REDIS CACHE UPDATED` after each response
- ⚡ `Performance: ~1-5ms (Fast!)` for cache hits

### Redis is NOT Working When You See:
- ⚠️ `REDIS CONNECTION FAILED` on startup
- ❌ Always seeing `REDIS CACHE MISS`
- ⚠️ `REDIS UPDATE FAILED`

## Performance Comparison

| Operation | Without Redis | With Redis (Hit) | Improvement |
|-----------|---------------|------------------|-------------|
| Load history | 50-100ms | 1-5ms | 20-100x faster |
| First message | 50-100ms | 50-100ms | Same (cache miss) |
| Next messages | 50-100ms | 1-5ms | 20-100x faster |

## Redis Operations in Chat Flow

1. **New Chat Session**
   - Check Redis → ❌ MISS
   - Load from MongoDB → ✅
   - Populate Redis → ✅
   - Generate response
   - Update Redis → ✅

2. **Existing Chat Session**
   - Check Redis → ✅ HIT (Fast!)
   - Use cached history
   - Generate response
   - Update Redis → ✅

3. **Delete Chat Session**
   - Delete from MongoDB
   - Clear Redis cache → ✅

## Manual Testing

### Check Health
```bash
curl http://localhost:5000/api/v1/health/redis
```

Expected response:
```json
{
  "service": "redis",
  "status": "healthy",
  "connected": true
}
```

### Send Chat Message
```bash
# Login first
curl -X POST http://localhost:5000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# Send message (watch server logs!)
curl -X POST http://localhost:5000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"question":"Hello!","session_id":null}'
```

## Troubleshooting

### No Redis Logs Showing
- Check if Redis is connected on startup
- Verify `.env` has correct Redis credentials
- Check `REDIS_HOST` and `REDIS_PASSWORD`

### Always Cache Miss
- Check Redis TTL (might be too short)
- Verify session_id is consistent
- Check Redis memory limits

### Cache Not Updating
- Check for Redis connection errors in logs
- Verify Redis is not full
- Check network connectivity

---

**Tip**: Keep the server terminal visible while running the demo to see all Redis operations in real-time!
