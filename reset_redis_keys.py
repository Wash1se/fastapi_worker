import redis
Redis = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
)

with Redis.pipeline() as pipe:
    pipe.multi()
    keys = Redis.keys('*')
    if keys:
        pipe.delete(*keys)
        result = pipe.execute()
