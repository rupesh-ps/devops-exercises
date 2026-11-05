# DevOps exercises

Hands-on exercises covering server provisioning, file transfers, and Linux process management. They use local Ubuntu VMs and MinIO for practice.

## 1. Cloud-init

Give a fresh Ubuntu VM one YAML file and let it install the required packages, create the application user and start a Dockerized HTTP app. The notes explain the boot stages, service recovery and what happens when provisioning runs again.

- [Setup and explanation](exercise-1-cloud-init/README.md)
- [Cloud-init configuration](exercise-1-cloud-init/cloud-init.yaml)

## 2. Rclone

Practise local and S3 transfers using two MinIO stores, without a saved Rclone configuration. This covers copy, move, sync, integrity checks, large uploads and recovery after interruptions. A small Bash script handles copy and sync with logs and failure exit codes.

- [Setup](exercise-2-rclone/README.md)
- [Commands used](exercise-2-rclone/commands.md)
- [Results and learnings](exercise-2-rclone/results.md)
- [Transfer script](exercise-2-rclone/transfer.sh)

## 3. Linux processes and systemd (Week 2)

Run a Python heartbeat worker from the shell, then manage it with systemd under a dedicated user. Work through signals, crashes, logs, resource limits and startup after reboot. The experiment notes include the results from testpress-vm and links to the screenshots.

- [Setup and explanation](exercise-3-process-management/README.md)
- [Worker application](exercise-3-process-management/app.py)
- [systemd unit](exercise-3-process-management/testpress-worker.service)
- [Experiments and observations](exercise-3-process-management/experiments.md)
- [Screenshots](exercise-3-process-management/evidence/README.md)

## Before starting

Cloud-init needs Multipass and internet access. Rclone needs Bash, Python 3, curl, rclone and Docker with Compose. Week 2 needs a Linux environment with systemd, Python 3 and cgroup v2. Each exercise's README has its setup steps.

Keep the MinIO `.env` file private. Generate credentials locally using the setup instructions.
