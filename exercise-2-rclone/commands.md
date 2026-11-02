# Commands used

Start Bash in this folder and export the settings for both stores. These define the connections for the current shell without creating an Rclone configuration file:

```bash
source .env
export RCLONE_CONFIG_LABA_TYPE=s3 RCLONE_CONFIG_LABA_PROVIDER=Minio
export RCLONE_CONFIG_LABA_ENDPOINT=http://127.0.0.1:19000 RCLONE_CONFIG_LABA_REGION=us-east-1
export RCLONE_CONFIG_LABA_ACCESS_KEY_ID="$MINIO_A_USER" RCLONE_CONFIG_LABA_SECRET_ACCESS_KEY="$MINIO_A_PASSWORD"
export RCLONE_CONFIG_LABB_TYPE=s3 RCLONE_CONFIG_LABB_PROVIDER=Minio
export RCLONE_CONFIG_LABB_ENDPOINT=http://127.0.0.1:19002 RCLONE_CONFIG_LABB_REGION=us-east-1
export RCLONE_CONFIG_LABB_ACCESS_KEY_ID="$MINIO_B_USER" RCLONE_CONFIG_LABB_SECRET_ACCESS_KEY="$MINIO_B_PASSWORD"
rc() { rclone --config /dev/null "$@"; }
```

## Sample files

The small text files and PDF are included. The existing 100 MiB and 1 GiB files are in `data/`. If either large file is missing, this creates it:

```bash
mkdir -p data/source data/large
cp -R samples/. data/source/
python3 - <<'PY'
import os
from pathlib import Path
for name,mib in [('data/source/sample-100MiB.bin',100),('data/large/video-1GiB.bin',1024)]:
    p=Path(name)
    if not p.exists():
        with p.open('wb') as f:
            for _ in range(mib): f.write(os.urandom(1024*1024))
PY
```

## Local copy, sync, move and delete

```bash
rc lsd data/source
rc ls data/source
bash transfer.sh copy data/source data/destination
bash transfer.sh copy data/source data/destination  # unchanged files skipped
printf 'Destination only\n' > data/destination/extra.txt
bash transfer.sh sync data/source data/destination  # preview
bash transfer.sh sync data/source data/destination --apply
rc check data/source data/destination

mkdir -p data/move
printf 'Disposable\n' > data/move/move-me.txt
rc move data/move data/moved
rc deletefile data/moved/move-me.txt --dry-run
rc deletefile data/moved/move-me.txt
```

Copy adds new files and replaces changed files at the same path, while leaving destination-only files alone. Move removes source files after they have been moved successfully. Sync also deletes files that exist only at the destination. The source comes first in the command, so check both paths before applying sync.

## S3 operations

```bash
rc mkdir laba:demo-practice
rc mkdir laba:demo-archive
rc mkdir labb:demo-practice
rc lsd laba:
bash transfer.sh copy data/source laba:demo-practice/files
rc lsf laba:demo-practice/files --recursive
rc copy laba:demo-practice/files data/download
rc check data/source data/download
rc copy laba:demo-practice/files laba:demo-archive/files -v  # server-side copy
rc copy laba:demo-practice/files labb:demo-practice/files -v # through this host
rc check laba:demo-practice/files labb:demo-practice/files --download
rc copyto data/source/notes.txt laba:demo-archive/delete-me.txt
rc deletefile laba:demo-archive/delete-me.txt --dry-run
rc deletefile laba:demo-archive/delete-me.txt
```

## On-the-fly remote and backend flags

These examples pass the credentials through the subshell's environment. The command arguments contain the connection settings:

```bash
(
  export AWS_ACCESS_KEY_ID="$MINIO_A_USER" AWS_SECRET_ACCESS_KEY="$MINIO_A_PASSWORD"
  rc lsf :s3:demo-practice/files --s3-provider Minio \
    --s3-endpoint http://127.0.0.1:19000 --s3-region us-east-1 --s3-env-auth
  rc lsf ':s3,provider=Minio,endpoint="http://127.0.0.1:19000",env_auth=true:demo-practice/files'
)
```

## Large upload, interruption and integrity

```bash
rc copy data/large laba:demo-practice/large --progress --stats 1s \
  --transfers 2 --checkers 4 --bwlimit 32M \
  --s3-upload-cutoff 8M --s3-chunk-size 8M --s3-upload-concurrency 2 \
  --retries 3 --low-level-retries 5
# Repeat it to observe unchanged files being skipped.
rc check data/large laba:demo-practice/large --download

# Start a fresh prefix, press Ctrl+C during upload, then repeat the command.
rc copy data/large laba:demo-practice/restart --bwlimit 8M --progress
rc backend list-multipart-uploads laba:demo-practice

bash transfer.sh copy data/nonexistent laba:demo-practice/failure
echo "Exit code: $?"
```

`--transfers` controls how many files transfer at once. S3 upload concurrency controls how many parts of one file upload at once. `32M` means about 32 MiB/s, and `check --download` reads the actual remote contents. The earlier test that stopped the storage endpoint is covered in results.md. Its verification harness has been removed.
