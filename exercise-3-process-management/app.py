import logging
import math
import os
import signal
import sys
import threading

log = logging.getLogger("testpress-worker")
stopping = threading.Event()
received_signal = None


def request_stop(signum, frame):
    global received_signal
    received_signal = signum
    stopping.set()


def read_settings():
    interval = float(os.environ.get("HEARTBEAT_SECONDS", "5"))
    crash_after = int(os.environ.get("CRASH_AFTER", "0"))
    memory_after = int(os.environ.get("MEMORY_AFTER", "0"))
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("HEARTBEAT_SECONDS must be a finite positive number")
    if crash_after < 0 or memory_after < 0:
        raise ValueError("CRASH_AFTER and MEMORY_AFTER must be zero or positive integers")
    if crash_after and memory_after:
        raise ValueError("Choose either CRASH_AFTER or MEMORY_AFTER, not both")
    return interval, crash_after, memory_after


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s pid=%(process)d %(message)s",
        stream=sys.stdout,
    )
    if os.geteuid() == 0:
        log.error("Run this worker as a non-root user")
        return 2
    try:
        interval, crash_after, memory_after = read_settings()
    except ValueError as error:
        log.error("Invalid configuration: %s", error)
        return 2

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    log.info(
        "Worker started uid=%s heartbeat_seconds=%s crash_after=%s memory_after=%s",
        os.geteuid(), interval, crash_after, memory_after,
    )
    heartbeats = 0
    allocations = []
    try:
        while not stopping.is_set():
            heartbeats += 1
            log.info("Heartbeat %s", heartbeats)
            if crash_after and heartbeats >= crash_after:
                log.error("Simulated crash at heartbeat %s", heartbeats)
                raise RuntimeError("Deliberate failure for the systemd experiment")
            if memory_after and heartbeats >= memory_after:
                block = bytearray(8 * 1024 * 1024)
                for offset in range(0, len(block), 4096):
                    block[offset] = 1
                allocations.append(block)
                log.info("Memory experiment: retaining %s MiB", len(allocations) * 8)
                if len(allocations) >= 16:
                    raise RuntimeError("Reached 128 MiB safety cap; check MemoryMax")
            stopping.wait(interval)
    finally:
        allocations.clear()
        block = None
    log.info("Received %s", signal.Signals(received_signal).name)
    log.info("Shutdown complete after %s heartbeats", heartbeats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
