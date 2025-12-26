# Scalability Notes

Some thoughts on how to scale this URL shortener when things get serious.

---

## Q1: What if logging becomes too expensive?

Right now, every redirect logs the IP and timestamp directly. That's fine for low traffic, but if we're hitting thousands of requests per second and need to send logs to an external service or separate database, doing it synchronously will kill our response times.

**What I'd do:**

1. **Use FastAPI's background tasks** for quick wins. Instead of `await log_to_external()`, just do `background_tasks.add_task(log_to_external, ip, timestamp)`. The response returns immediately and logging happens after.

2. **For heavier load, use a message queue.** Push log entries to Redis (with `lpush`) or RabbitMQ, then have a separate worker process that consumes and batches them. Something like:
   ```
   Request comes in → Push to queue → Return 307 immediately
   Worker picks up → Batches 100 entries → Bulk insert to logs DB
   ```

3. **Batching is key.** Instead of 1000 individual DB inserts, batch them into groups of 50-100. Way less overhead.

4. **If we're going full observability**, just ship logs to something like Loki or Elasticsearch via a lightweight agent (Fluentd, Vector). The app just writes to stdout/file, agent handles the rest. Zero impact on request latency.

The main idea: don't let logging block the response. Fire and forget, process later.

---

## Q2: What changes for multi-instance deployment?

If we deploy this on multiple servers behind a load balancer, a few things need attention:

**What needs to become external:**

- **Database** - Already external (PostgreSQL), so we're good. Just make sure connection pooling is configured properly per instance (we have `DB_POOL_SIZE=5` per instance, not shared).

- **Cache (if we add one)** - Can't use in-memory cache anymore. Need Redis or Memcached that all instances talk to.

- **Session/state** - We're stateless, so no issue here. But if we ever add rate limiting, that counter needs to be in Redis, not memory.

**Risks to manage:**

- **Race conditions on short code generation.** Two instances might generate the same code at the same moment. We handle this with unique constraint + retry logic, but worth monitoring.

- **Connection pool exhaustion.** 5 pools × 4 instances = 20 connections. Make sure PostgreSQL's `max_connections` can handle it, plus some buffer.

- **Log aggregation.** Logs are now spread across instances. Need centralized logging (ELK, Loki, CloudWatch) to make sense of anything.

- **Health checks.** Load balancer needs to hit `/healthz` and `/readyz` properly. If one instance loses DB connection, it should be removed from rotation.

**What stays the same:**

The app itself doesn't change much. It's already stateless and async. Main work is infrastructure: load balancer config, shared Redis, centralized logging.

---

## Q3: How to survive a traffic spike? (campaign scenario)

Let's say marketing runs a campaign and we suddenly get 5000+ requests per second. Here's the plan:

**Immediate priorities:**

1. **Async DB operations** - Already using `asyncpg`, which is good. We're not blocking on DB calls.

2. **Connection pooling** - Already configured. Might need to bump `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` depending on expected load. Also check PostgreSQL's `max_connections`.

3. **Caching hot URLs** - This is the biggest win. Most traffic will hit a few popular short codes. Cache them in Redis with 1-hour TTL:
   ```
   cache hit → return immediately (no DB)
   cache miss → query DB → cache result → return
   ```
   This alone can drop DB load by 80-90% during a campaign.

4. **Queue-based logging** - As mentioned above, don't let analytics slow down redirects. Push to queue, process async.

5. **Rate limiting** - Protect against abuse. Maybe 1000 req/min per IP for `/shorten`, unlimited for redirects (since that's the whole point).

**If things get really hot:**

- Add more app instances (horizontal scaling). Since we're stateless, just spin up more containers.
- Read replicas for PostgreSQL if stats queries are heavy.
- CDN in front for redirect caching (if URLs don't change often).

**What I've already done:**

- Async everywhere (FastAPI + asyncpg)
- Connection pooling configured
- Indexes on hot columns (`short_code`, `url_id`, `day`)
- Stateless design (easy to scale horizontally)

**What I'd add before a big campaign:**

- Redis cache for URL lookups
- Queue for visit logging (Redis + worker)
- More instances behind load balancer
- Alerting on response times and error rates

---