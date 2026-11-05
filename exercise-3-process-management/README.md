# Week 2. Linux processes and systemd

A small Python worker logs a heartbeat every five seconds. Goal is to get understanding of signals, then systemd to check startup services, restarts, logs and memory limits.

- [What happened in each experiment](experiments.md)
- [Screenshot index](evidence/README.md)

## Setup

From the repo root on the Mac, copy the exercise to the existing VM.

```bash
multipass transfer -r exercise-3-process-management testpress-vm:/home/ubuntu/
multipass shell testpress-vm
```

Inside the VM, run these as your normal login user.

```bash
cd ~/exercise-3-process-management
ps -p 1 
sudo apt-get update
sudo apt-get install -y python3 procps psmisc htop nano
```

The checks should show `systemd` is main process with `PID 1`. If the service account already exists, skip the first command below.

```bash
sudo adduser --system --group testpress-worker
sudo mkdir -p /opt/testpress-worker
sudo cp app.py /opt/testpress-worker/app.py
sudo cp worker.env.example /etc/testpress-worker.env
sudo chown root:testpress-worker /etc/testpress-worker.env
sudo chmod 640 /etc/testpress-worker.env
sudo cp testpress-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
```

Use `python3 -u app.py` for the manual tests. When ready to run it through systemd, use:

```bash
sudo systemctl enable testpress-worker
sudo systemctl start testpress-worker
systemctl status testpress-worker --no-pager
```

## How it works

| Setting | What it does |
| --- | --- |
| `HEARTBEAT_SECONDS=5` | Logs immediately, then about every five seconds |
| `CRASH_AFTER=0` | Turns off the deliberate crash |
| `MEMORY_AFTER=0` | Turns off the 8 MiB allocation per heartbeat |

systemd loads these settings from `/etc/testpress-worker.env` when it starts Python. Restart the service after changing the environment file. Run `sudo systemctl daemon-reload` after editing the unit.

The worker runs in the foreground under `testpress-worker`. SIGTERM and SIGINT wake its wait and let it exit cleanly. `Restart=on-failure` retries unexpected failures after three seconds. Three starts are allowed in 30 seconds. `Type=exec` checks that systemd could launch the executable. [systemd service settings](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)

The service sends logs to journald and limits CPU time to a quarter of one CPU. Memory pressure starts at 48 MiB, with a hard limit of 64 MiB and no swap allowance. [systemd resource limits](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html)
