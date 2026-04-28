# Redis Datastore Persistence (`persistent_storage`)

This folder (or any path you pass to `run-redis --data-dir <PATH>`) is a host bind mount for Redis container path `/data`.

When Redis Stack starts, it reads persistence files from this directory if they already exist. New writes then update these files.

## Typical generated files

You may see one or more of the following:

- `appendonlydir/appendonly.aof.manifest`
  - A small metadata file used by Redis 7+ AOF multipart mode.
  - It tells Redis which AOF base/increment files belong to the active dataset.

- `appendonlydir/appendonly.aof.*.base.rdb`
  - Base snapshot segment for AOF history (RDB-encoded base).
  - Used as the starting point when reconstructing state.

- `appendonlydir/appendonly.aof.*.incr.aof`
  - Incremental AOF command log segments (write operations after the base file).
  - Redis replays these to reach the latest state.

- `dump.rdb` (optional)
  - Point-in-time snapshot file if RDB snapshots are enabled by config/image defaults.

## How startup/loading works

With `run-redis --data-dir ...`, this project enables `--appendonly yes` by default.

On Redis startup:

1. Redis checks `/data` (your mounted host directory).
2. If AOF files exist and are valid, Redis reconstructs state from AOF (manifest + base + incr).
3. If configured, RDB snapshots may also be used/maintained.
4. Redis starts serving with the recovered dataset.

This means data is **loaded**, not automatically overwritten.

## When data can be lost or changed unexpectedly

Data persistence is durable, but data can still be changed/lost if you:

- Point `--data-dir` at a different directory.
- Manually delete files under the persistence directory.
- Run destructive Redis commands (`FLUSHDB`, `FLUSHALL`, key deletions).
- Change namespace/version/developer segments in app logic and then clean those segments.
- Recreate container with different settings and a different mount path.

## How to inspect actual stored data

The files are internal Redis persistence formats, not app-level JSON/CSV.
Use Redis tools to inspect logical keys/values:

```bash
redis-cli -h 127.0.0.1 -p 6379 -a changemeplease
INFO keyspace
SCAN 0 MATCH * COUNT 100
```

Or use RedisInsight on port `8001` if enabled.

## Ways to run the datastore

`run-redis` starts Redis Stack (unless skipped) and then starts the SIC datastore service.

### 1) Recommended: use a `redis.conf` file

```bash
run-redis \
  --data-dir /absolute/path/to/persistent_storage \
  --redis-conf /absolute/path/to/redis.conf
```

- Mounts the config file to `/redis-stack.conf`
- Starts Redis using that config file
- Prefer this for explicit, versioned control of persistence/password/memory settings

### 2) Default local run (ephemeral container data)

```bash
run-redis
```

- Uses container `sic-redis-stack`
- Uses image `redis/redis-stack:latest`
- Publishes Redis on `6379`, RedisInsight on `8001`
- No host data mount (container-local persistence only)

### 3) Persistent host directory

```bash
run-redis --data-dir /absolute/path/to/persistent_storage
```

- Mounts host directory to `/data`
- Enables AOF by default (`--appendonly yes`) when no custom `--redis-args` is provided

### 4) Pass Redis server arguments directly

```bash
run-redis \
  --data-dir /absolute/path/to/persistent_storage \
  --redis-args "--requirepass changemeplease --appendonly yes --save 60 1000"
```

- Sets `REDIS_ARGS` for the Redis Stack container
- Useful for tuning persistence and memory behavior without a config file

### Creating Redis configuration (`redis.conf`)

Use a config file when you want one place to control persistence, passwords, memory,
or other server behavior.

Example `redis.conf`:

```conf
# --- Security ---
requirepass changemeplease

# --- Persistence location ---
dir /data
dbfilename dump.rdb

# --- RDB snapshot rules ---
# save <seconds> <changes>
save 900 1
save 300 10
save 60 10000

# RDB behavior
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes

# --- AOF persistence ---
appendonly yes
appenddirname appendonlydir

# Optional AOF tuning
appendfsync everysec
```

Run with:

```bash
run-redis \
  --data-dir /absolute/path/to/persistent_storage \
  --redis-conf /absolute/path/to/redis.conf
```

Notes:

- `dir /data` is important when using `--data-dir`, because `/data` is the container
  path mounted to your host folder.
- RDB generation is controlled by the `save` lines.
- If you do not want RDB snapshots, set:
  - `save ""`
  and keep AOF (`appendonly yes`) if you still want persistence.

### 5) Use an existing Redis Stack container / external Redis

```bash
run-redis --skip-docker
```

- Skips Docker management
- Starts only the SIC datastore service, assuming Redis is already reachable

### 6) Custom ports, name, or image

```bash
run-redis \
  --container-name sic-redis-stack-dev \
  --host-port 6380 \
  --insight-port 8002 \
  --image redis/redis-stack:latest
```

- Useful when running multiple local Redis instances

## Notes on argument changes

- If a container with the same `--container-name` already exists, `run-redis` compares its config (ports, mounts, image, args/config) with your requested arguments.
- If they differ, it recreates the container with the new arguments before launching the datastore service.
