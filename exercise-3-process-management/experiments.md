# Week 2 experiments

For setup, use the [README](README.md).

## 1. Find the Python process

In the first Linux terminal I ran `python3 -u app.py`. In the second I checked it with:

```bash
ps -C python3 -o pid,ppid,user,stat,args
```

**Expected.** A heartbeat every five seconds and a process owned by my login user.

**Observed.** The worker printed heartbeats about five seconds apart. `ps` showed PID 6330, parent PID 1347, user `ubuntu` and state `S+`.

**Why.** The worker spends most of its time waiting between heartbeats. `S` means sleeping and `+` marks the foreground process group.

[Heartbeats](evidence/01-running-process-heartbeats.png) · [Process details](evidence/01-running-process.png)

## 2. Stop it with SIGTERM

```bash
kill -TERM 6330
```

**Expected.** The worker would log shutdown and exit cleanly.

**Observed.** PID 6330 logged `Received SIGTERM` and `Shutdown complete after 22 heartbeats`. In the terminal that ran Python, `echo $?` printed `0`.

**Why.** The signal handler wakes the waiting loop so Python can finish its cleanup.

[Signal command](evidence/02-sigterm-command.png) · [Shutdown and exit code](evidence/02-sigterm.png)

## 3. Stop a new worker with SIGKILL

I started another copy with `python3 -u app.py`, then used its PID in the second terminal.

```bash
pgrep -af app.py
kill -KILL 6459
```

**Expected.** The worker would disappear without a shutdown message.

**Observed.** PID 6459 printed five heartbeats, then the shell showed `Killed`. The exit code was `137`.

**Why.** SIGKILL ends the process immediately. Bash reports 128 plus the signal number, which is 9 here.

[Signal command](evidence/03-sigkill-command.png) · [Termination and exit code](evidence/03-sigkill.png)

## 4. Run it as a service

```bash
sudo systemctl enable testpress-worker
sudo systemctl start testpress-worker
systemctl status testpress-worker --no-pager
sudo journalctl -u testpress-worker -n 15 --no-pager
```

**Expected.** The service would be enabled and running, with heartbeats in the journal.

**Observed.** Status showed `enabled`, `active (running)` and Python PID 6572. The journal showed its heartbeats.

**Why.** `start` runs the service now and `enable` arranges startup at boot. The unit sends the app's output to journald.

[Service status and heartbeats](evidence/04-service-running.png)

## 5. Check automatic restart

```bash
systemctl show testpress-worker -p MainPID -p NRestarts
sudo kill -KILL 6572
systemctl show testpress-worker -p MainPID -p NRestarts
```

**Expected.** systemd would start a new process after the failure.

**Observed.** The PID changed from 6572 to 6743 and `NRestarts` went from 0 to 1. The replacement worker was running and logging heartbeats.

**Why.** `Restart=on-failure` handles SIGKILL as a failure. The unit waits three seconds before restarting.

[Before and after the restart](evidence/05-auto-restart.png)

## 6. Crash inside Python

I set `CRASH_AFTER=3` in `/etc/testpress-worker.env` and ran the service with that setting.

```bash
sudo journalctl -u testpress-worker -n 40 --no-pager
systemctl show testpress-worker -p MainPID -p NRestarts
```

**Expected.** Python would raise an error at heartbeat 3 and systemd would retry.

**Observed.** PID 7229 logged the deliberate `RuntimeError` at heartbeat 3 and exited with `1/FAILURE`. The journal showed restart attempts. The final query showed `MainPID=0` and `NRestarts=5`.

**Why.** The unhandled exception caused the failure. Ubuntu's Apport hook also tried to write under `/var/crash` and hit the service's read-only filesystem. That error came after the deliberate exception.

[Traceback and restart attempts](evidence/06-crash-logs.png)

## 7. Use an invalid Python path

I changed the installed unit's `ExecStart` to use `/incorrectpath/bin/python3`.

```bash
sudo systemctl daemon-reload
sudo systemctl reset-failed testpress-worker
sudo systemctl start testpress-worker
systemctl status testpress-worker --no-pager
```

**Expected.** systemd would fail to start Python.

**Observed.** Status showed `203/EXEC`. The journal later showed repeated attempts with the same execution error and `Start request repeated too quickly`.

**Why.** systemd couldn't execute the configured path. The failure happened before the worker could log a heartbeat.

[Edited path](evidence/07-invalid-executable-edited-path.png) · [Failed status](evidence/07-invalid-executable.png) · [Retry log](evidence/07-invalid-executable-retry-limit.png)

## 8. Hit the start limit with application crashes

I ran the worker with `CRASH_AFTER=1` and checked the result.

```bash
systemctl show testpress-worker -p Result -p NRestarts
sudo journalctl -u testpress-worker -n 40 --no-pager
```

**Expected.** Repeated failures would eventually make systemd refuse another start.

**Observed.** The worker failed on heartbeat 1. The journal showed `Start request repeated too quickly`. The property query reported `Result=exit-code` and `NRestarts=3`.

**Why.** The unit allows three starts within 30 seconds. The journal shows that the limit intervened even though the reported result was `exit-code`.

[Crash loop and start limit](evidence/08-restart-limit.png)

## 9. Exceed the memory limit

I ran with `MEMORY_AFTER=1` and checked the limits and journal.

```bash
systemctl show testpress-worker -p MemoryHigh -p MemoryMax -p CPUQuotaPerSecUSec
systemctl show testpress-worker -p MemoryCurrent -p Result
sudo journalctl -u testpress-worker -n 40 --no-pager
```

**Expected.** Memory usage would grow until the cgroup could no longer keep it within the limit.

**Observed.** The limits were 48 MiB for `MemoryHigh`, 64 MiB for `MemoryMax` and 250 ms of CPU time per second. One reading showed 62,492,672 bytes in use. The worker logged 56 MiB of retained blocks before the OOM killer terminated PID 9236. systemd reported `oom-kill` and `9/KILL`.

**Why.** The memory limit applies to the whole service, including Python's own memory. The CPU setting shows the configured quota.

[Limits and memory readings](evidence/09-memory-limit.png) · [OOM journal](evidence/09-memory-limit-oom-journal.png)

## 10. Check startup after reboot

I checked that both failure triggers were zero, enabled the service and rebooted. After reconnecting with `multipass shell testpress-vm`, I checked the new boot.

```bash
uptime -s
cat /proc/sys/kernel/random/boot_id
systemctl status testpress-worker --no-pager
sudo journalctl -b -u testpress-worker -n 15 --no-pager
```

**Expected.** The boot ID would change and systemd would start the worker during boot.

**Observed.** Boot time changed from 08:04:34 to 10:24:46 IST and the boot ID changed. The service was enabled and running as PID 662 from 10:24:51 IST. The journal showed new heartbeats with both failure triggers at zero.

**Why.** The enabled unit starts through `multi-user.target`. The boot ID and the service start time show the new run.

[Before reboot](evidence/10-before-reboot.png) · [After reboot](evidence/10-after-reboot.png)

## Other commands to practise

These are separate from the ten screenshot results. Run the foreground worker, press Ctrl+Z, use `jobs` to see its job number, then try `bg %1` and `fg %1` if it is job 1. Ctrl+C stops it through SIGINT.

Try `top`, `htop`, `pidof python3` and `pstree` to find or inspect the worker. `nohup python3 -u app.py &` keeps the command running through a hangup. Use `pgrep -af app.py` to find your command and stop it by PID. For a scoped `pkill` test, close other manual copies first and use `pkill -TERM -f '^python3 -u app.py$'`.

Run `nice -n 10 python3 -u app.py` in one terminal. In the other, find its PID and try `renice -n 15 -p 12345` with your actual PID. Compare the nice value with `ps -C python3 -o pid,ni,args`. A higher nice value lowers scheduling priority.

For systemd, try `systemctl stop`, `restart`, `disable` and `enable` with `testpress-worker`. Re-enable the worker after the test. `systemd-analyze time` shows boot timing.
