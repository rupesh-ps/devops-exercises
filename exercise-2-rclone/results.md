# Practice results

These results are from the practice run on 1 November 2026, using rclone 1.71.0 on macOS ARM64, Docker/Colima and two local MinIO services. The test harness was removed afterwards. The speeds below are from local storage, so they don't tell us what to expect over a cloud network.

| Experiment | Observed result |
| --- | --- |
| Local copy | Four files, about 100 MiB; second copy transferred 0 bytes and kept the destination-only file |
| Changed-content sync | Preview left the extra file; actual sync updated the changed file and deleted the extra |
| Move/delete | Disposable source removed after move; deletion preview retained its file; actual deletion removed it |
| Corruption | Changed bytes while preserving size/time; `check` detected the mismatch; `copy --checksum` repaired it |
| S3 upload/download | Four matching files, zero differences; second upload transferred 0 bytes |
| Configuration-free access | Runtime named remotes, `:s3:` flags, inline connection string and an empty configuration worked |
| Same-endpoint copy | Four server-side copies, about 100 MiB |
| Separate endpoints | About 100 MiB through the Rclone host; no server-side copies; integrity check passed |
| Large upload | 1 GiB plus a 52-byte marker in 33.30 seconds, capped at 32 MiB/s |
| Repeated large upload | 0 bytes transferred; two files checked |
| Interrupted upload | SIGINT after six seconds; exit 130; completed marker visible, large object absent |
| Restarted upload | Full 1,073,741,824 bytes transferred again in 33.26 seconds; marker skipped; contents matched |
| Real endpoint outage | Same process recovered on attempt 4 after store A was stopped and restarted |
| Retry integrity | Downloaded SHA-256 matched; 80 MiB transferred for a 64 MiB file because failed work was repeated |
| Failure handling | Missing source returned exit 3; wrong credentials returned HTTP 403 and exit 1 |

## Learned so far

Copy keeps files that exist only at the destination, but it can overwrite a changed file at the same path. Move removes source files after a successful move. Sync goes further and deletes destination-only files to make the two sides match.
Matching size and modification time can make Rclone skip a file. That doesn't mean it has read and compared all the contents. `check --download` does that comparison with the remote data. A multipart ETag also isn't an ordinary MD5 hash of the file.
The restart test uploaded the interrupted large object from the beginning. In the outage test, the same process stayed alive and recovered through retries. Those are different cases, and neither result proves that a new process resumed the old multipart upload.
Copying between compatible buckets on the same endpoint can happen inside storage. Between the two separate endpoints here, the data passed through the host, without an intermediate file on disk.
The commands worked without a saved rclone.conf. One thing that came up during practice was DEBUG logging printing credential settings. Those values were redacted from the shared evidence, and the script uses INFO logging.
For Celery, the approach is to pass an argument list and a separate child-process `env` to `subprocess.run(..., check=True, timeout=...)`. That avoids changing global environment variables for each task. The earlier example uploaded successfully and left its parent's environment unchanged.

The smaller transfer.sh keeps copy and sync, with a preview before applying sync. It still shows progress, retries transfers, writes logs and returns failure codes. Local copy, sync preview/apply and the missing-source case were checked separately during cleanup. The raw experiment logs and old automation are backed up outside this folder.
