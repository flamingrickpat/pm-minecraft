from concurrent.futures import ThreadPoolExecutor
from threading import Event
import time

from mcmcp.runtime import MinecraftRuntime


def runtime_without_body():
    runtime = MinecraftRuntime.__new__(MinecraftRuntime)
    runtime._stop_generation = 0
    runtime.body = None
    return runtime


def test_wait_times_out_with_latest_observation():
    runtime = runtime_without_body()
    started = time.monotonic()
    value, reason = runtime._wait_until(lambda: 7, lambda value: value == 8, 0.05, 0)
    assert (value, reason) == (7, "timeout")
    assert time.monotonic() - started < 1


def test_wait_succeeds_when_state_changes():
    runtime = runtime_without_body()
    observations = iter([1, 2, 3])
    assert runtime._wait_until(lambda: next(observations), lambda value: value == 3, 1, 0) == (3, None)


def test_command_stop_interrupts_wait_but_skill_stop_does_not():
    runtime = runtime_without_body()
    entered = Event()

    def read():
        entered.set()
        return 7

    with ThreadPoolExecutor() as pool:
        waiting = pool.submit(runtime._wait_until, read, lambda value: False, 5, 0)
        assert entered.wait(1)
        runtime.minecraft_stop("skill")
        assert runtime._stop_generation == 0
        runtime.minecraft_stop("command")
        assert waiting.result(timeout=1) == (7, "stopped")
    assert runtime._wait_until(lambda: 8, lambda value: True, 1, runtime._stop_generation) == (8, None)
