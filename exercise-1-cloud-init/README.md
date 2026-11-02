# Exercise 1: Cloud-init

The idea here is to give a fresh Ubuntu VM one YAML file and let it do the setup. It installs Docker, Git, curl and FFmpeg, creates `testpress`, and starts a small HTTP app. There's no need to log in and install or configure things by hand.

Ubuntu is already installed in the image that Multipass launches. Cloud-init runs during boot and prepares that installed system.

## Run

You'll need Multipass and an internet connection. Run this from the exercise folder, using a VM name that isn't already taken:

```bash
multipass launch 24.04 --name rupesh-cloud-init-02 \
  --cpus 2 --memory 2G --disk 12G --timeout 900 \
  --cloud-init cloud-init.yaml
multipass exec rupesh-cloud-init-02 -- sudo cloud-init status --wait --long
```

The earlier practice VM is `rupesh-cloud-init-01`. Use its name in [commands.md](commands.md), or replace it with the name of a new VM. [results.md](results.md) has the recorded outputs and observations.

## How the setup fits together

```text
Multipass creates Ubuntu VM
  -> cloud-init installs packages, creates the user and writes files
  -> the provisioning script builds the Docker image
  -> systemd starts the container
  -> the app responds on VM port 8080
```

Cloud-init prepares the host. The Dockerfile describes the app image. systemd starts the app and brings it back after it exits. Each part has a separate job, which also helps when tracing a failure.

## What happens during boot

The order of sections in the YAML isn't the execution order. Cloud-init runs modules in stages, using the module lists in the image's `/etc/cloud/cloud.cfg`.

| Stage | What happens |
| --- | --- |
| Detect | Decide whether cloud-init should run on this platform |
| Local | Find local datasource information and prepare networking |
| Network | Process user-data and early modules; on this Ubuntu image, these include users/groups and ordinary file writing |
| Config | Run configuration modules; `runcmd` writes a script here |
| Final | Install packages and execute user scripts, including the generated `runcmd` script through `scripts_user` |

`runcmd` preparing a script and `scripts_user` executing it are separate steps. That's why the repeat-execution check includes both modules. See the [boot stages](https://docs.cloud-init.io/en/latest/explanation/boot.html) and [runcmd reference](https://docs.cloud-init.io/en/latest/reference/modules.html#runcmd).

A stage isn't simply "first boot only" or "every boot". Individual modules have their own frequencies. Our users/groups, file writing, package setup, runcmd and user-script modules normally run once per instance. `bootcmd` and per-boot scripts are examples that can run every boot; this setup doesn't need them.

## How it recognises the same VM

The datasource supplies an instance ID. With the normal cache-check behavior, cloud-init compares it with the cached identity under `/var/lib/cloud`. Per-instance module markers are under `/var/lib/cloud/instance/sem/`.

On the same instance, completed per-instance modules are normally skipped. A changed instance identity or missing cache can trigger first-boot work again. Cache-trust settings can change that behavior. The `boot-finished` file records completion; it isn't the only thing deciding what runs. The [first-boot explanation](https://docs.cloud-init.io/en/latest/explanation/first_boot.html) covers this distinction.

Our YAML is user-data: what to configure. Metadata describes the instance, including its identity. Multipass supplied these through NoCloud in the recorded run. QEMU can also supply NoCloud data using a seed disk containing files named `user-data` and `meta-data`.

## Why the YAML is written this way

`package_update: true` refreshes the package index. `package_upgrade: false` avoids a general OS upgrade, while `packages` installs the four required packages.

The default cloud user stays available for Multipass. `testpress` has a locked password, Bash as its shell and membership in the Docker group. `ssh_pwauth: false` disables password-based SSH. Docker group membership still gives effectively root-level control of the VM; it isn't a low-privilege permission.

`write_files` creates the app code, Dockerfile, environment file, service and provisioning script. Keeping these inside the YAML avoids separate copies drifting apart. Files initially belong to `root:root`, so file creation doesn't depend on `testpress` already existing. The final script changes `/opt/testpress` to `root:testpress`, mode `0750`, and `app.env` to `root:testpress`, mode `0640`.

For `0640`, the owner can read/write, the group can read, and other users have no access. The explicit `!!str` makes the permission a YAML string. It worked around a Multipass 1.15.1 serialization bug. Multipass 1.17.0's [serializer preserves quoted permission values](https://github.com/canonical/multipass/blob/v1.17.0/src/utils/yaml_node_utils.cpp), so ordinary `"0640"` is sufficient there. The current YAML retains the explicit tags.

The app reads `MESSAGE` and `APP_PORT` from its environment. `/` returns the greeting, `/health` returns `ok`, and other paths return 404. `APP_ENV` is a sample setting; the code doesn't use it. Port 8080 also appears in the Docker port mapping and health check, so changing it needs those settings to agree.

The Dockerfile pins the Python base image by digest and runs the app as UID/GID `10001:10001`. That container user is separate from the VM user `testpress`. `EXPOSE 8080` documents the container port; `--publish=8080:8080` makes it reachable through the VM. The container also uses a read-only root filesystem, dropped capabilities and `no-new-privileges`.

## Startup, recovery and readiness

The service requires Docker and starts after it. Docker runs in the foreground, so systemd can track its process. When the app and container exit, the attached Docker command exits too. `Restart=always` brings the service back after three seconds. The service removes the old named container before creating its replacement.

Docker's own restart policy is `no`, leaving systemd responsible for restarts. This avoids two managers trying to handle the same container. [Docker's restart documentation](https://docs.docker.com/engine/containers/start-containers-automatically/) explains the interaction.

`systemctl enable` arranges startup on future boots. `systemctl start` starts the service now. Rebooting therefore starts the app without rerunning the image build. Ten service starts within a minute can trigger the configured start limit.

Starting a service doesn't prove that HTTP is ready. The provisioning script polls `/health` before reporting success. Docker's health check also calls `/health`, using Python already present in the image. If the app stays alive but hangs, it can become unhealthy without systemd restarting it. Health reporting and process recovery check different things.

## What repeating the setup proves

A normal reboot skips completed modules, so it doesn't prove the provisioning commands are safe to repeat. The manual checks force the relevant modules to execute again and compare identity, file contents, permissions and Docker IDs.

Files are written to fixed paths, Docker reuses unchanged build layers, and starting an already-running service leaves its container alone. This checks an unchanged rerun. Editing the host YAML doesn't update an existing VM, and changing app inputs needs an explicit rebuild/restart workflow. The Python image is pinned, but apt repositories and the Ubuntu VM image can still change over time.
