"""
Module to configure and run a Celery Worker for executing FIO benchmarks.

This module initializes a Celery application, configures its broker and backend
using environment variables, and provides a Worker class to manage worker
registration, starting, and task execution. Additionally, it registers  a Celery
task to run FIO benchmarks.

Imports:
    os: Provides a way of using operating system dependent functionality.
    socket: Provides access to the BSD socket interface.
    typing: Provides various tools for type hinting.
    redis: Python client for Redis.
    celery: An asynchronous task queue/job queue based on distributed message
            passing.
    dotenv: Reads key-value pairs from a .env file and sets them as environment
            variables.

Classes:
    Worker: Manages the lifecycle and operations of a Celery worker, including
            registration, initialization, and task execution.
"""

import os
import socket
from typing import Any, Self

import redis
from celery import Celery
from dotenv import load_dotenv


class Worker:
    """
    Manages a Celery worker's configuration, registration, and task execution.

    The Worker class encapsulates the setup and management of a Celery worker.
    It initializes the worker with configuration details from environment
    variables, supports worker registration in a Redis set, and starts the
    worker with specified parameters including a direct queue.
    The class also ensures cleanup by un-registering the worker upon deletion.

    Attributes:
        app (Celery): An instance of the Celery application.
        redis_host (str | None): Redis server host.
        redis_port (str | None): Redis server port.
        r (redis.Redis): Redis client instance for worker registration management.
        worker_group (str | None): Group this worker belongs to.
        worker_id (str | None): ID of the worker.

    Methods:
        register_worker(worker_group: str, worker_id: str) -> Self:
            Registers the worker in a Redis set under the specified group.

        start_worker() -> None:
            Starts the Celery worker with the given configuration.

        get_workers(worker_group: str) -> set[Any]:
            Retrieves a set of workers registered under the specified group.

        __del__() -> None:
            Ensures the worker is unregistered from the Redis set upon object deletion.
    """

    app: Celery

    def __init__(self) -> None:
        load_dotenv()

        self.redis_host: str | None = os.getenv("REDIS_HOST")
        self.redis_port: str | None = os.getenv("REDIS_PORT")
        self.redis_url: str = f"redis://{self.redis_host}:{self.redis_port}/0"

        self.r = redis.Redis(host=self.redis_host, port=self.redis_port)

        self.worker_group: str | None = None
        self.worker_id: str | None = None

        self.app: Celery = Celery(
            "fio",
            broker=self.redis_url,
            backend=self.redis_url,
        )

        self.app.conf.update(
            result_expires=None,  # This will ensure that results won't expire
        )

    def register_worker(self, worker_group: str, worker_id: str) -> Self:
        self.worker_id = worker_id
        self.worker_group = worker_group

        self.r.sadd(f"workers_{self.worker_group}", self.worker_id)

        print(f"Registered worker {self.worker_id} for group {self.worker_group}")

        return self

    def start_worker(self) -> None:
        if self.worker_id is None:
            raise ValueError("worker_id must be set before starting the worker")
        self.app.worker_main(["worker", "--loglevel=info", "-E", "-Q", self.worker_id])
        self.__del__()  # pylint: disable=unnecessary-dunder-call

    def __del__(self) -> None:
        if self.worker_group is not None and self.worker_id is not None:
            print(
                f"Unregistering worker {self.worker_id} for group {self.worker_group}"
            )
            self.r.srem(f"workers_{self.worker_group}", self.worker_id)
        else:
            pass

    def get_workers(self, worker_group: str) -> set[Any]:
        return self.r.smembers(f"workers_{worker_group}")  # type: ignore[return-value]


worker = Worker()
hostname: str = socket.gethostname()


@worker.app.task(name="celery_app.run_benchmark")
# def run_benchmark(filename: str, wave_id: str, timestamp: datetime.datetime) -> dict:
def run_benchmark() -> dict:
    raise NotImplementedError
    # TODO: Add worker id group@host
    # return {"status": "Passed", "test": [1, 2, 3, 4]}
