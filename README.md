# DevOps exercises

Two hands-on exercises covering server provisioning with cloud-init and file transfers with Rclone. Both run locally, using Ubuntu VMs and MinIO instead of paid cloud services.

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

## Before starting

Cloud-init needs Multipass and internet access. Rclone needs Bash, Python 3, curl, rclone and Docker with Compose. Each exercise's README has its setup steps.

Keep the MinIO `.env` file private. Generate credentials locally using the setup instructions.
