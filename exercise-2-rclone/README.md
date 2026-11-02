# Exercise 2: Rclone

This exercise uses local folders and two MinIO stores to practise copying, syncing and checking files. Every S3 command runs with the saved Rclone configuration disabled.

The folder has the transfer script, Compose file, small samples and these notes. The large practice files are in `data/`, which Git ignores.

## Setup

You'll need Bash, Python 3, curl, rclone and Docker with Compose. The private `.env` already has separate credentials for the two stores. If you're starting from a fresh copy, generate it once:

```bash
# Run from this folder. Don't replace an existing .env.
if [ ! -f .env ]; then
  (umask 077; python3 - <<'PY'
import secrets
from pathlib import Path
Path('.env').write_text('\n'.join(f'MINIO_{store}_{key}={secrets.token_hex(16)}' for store in ('A','B') for key in ('USER','PASSWORD'))+'\n')
PY
  )
fi
docker compose up -d
```

Store A runs at `127.0.0.1:19000` and store B at `127.0.0.1:19002`. Both bind to localhost. The commands work without opening either console.

[commands.md](commands.md) has the connection settings and practice commands. The transfer results and failure tests are in [results.md](results.md).

## Transfer script

```bash
bash transfer.sh copy data/source laba:demo-practice/files
bash transfer.sh sync data/source laba:demo-practice/files          # preview
bash transfer.sh sync data/source laba:demo-practice/files --apply  # execute
```

The script shows progress, writes an INFO log, retries failed transfers and returns the failure code if the transfer doesn't succeed. Sync only previews changes unless `--apply` is passed. Connection settings come from the shell, so it doesn't need an `rclone.conf` file. The bandwidth and concurrency experiments use Rclone commands directly.

Keep `.env` private. This lab uses administrative credentials; for production, use restricted credentials that expire where possible. DEBUG logs can also print credential settings, so environment variables still need careful handling.

Use `docker compose stop` to pause the lab. Once you're finished with the stored objects, `docker compose down --volumes` removes them. It leaves the local files alone.
