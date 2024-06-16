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
        rabbitmq_host (str | None): RabbitMQ server host.
        rabbitmq_port (str | None): RabbitMQ server port.
        rabbitmq_username (str | None): RabbitMQ server username.
        rabbitmq_password (str | None): RabbitMQ server password.
        rabbitmq_vhost (str | None): RabbitMQ virtual host.
        postgresql_host (str | None): PostgreSQL server host.
        postgresql_port (str | None): PostgreSQL server port.
        postgresql_username (str | None): PostgreSQL server username.
        postgresql_password (str | None): PostgreSQL server password.
        postgresql_database (str | None): PostgreSQL database name.
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

        self.rabbitmq_host: str | None = os.getenv("RABBITMQ_HOST")
        self.rabbitmq_port: str | None = os.getenv("RABBITMQ_PORT")
        self.rabbitmq_username: str | None = os.getenv("RABBITMQ_USERNAME")
        self.rabbitmq_password: str | None = os.getenv("RABBITMQ_PASSWORD")
        self.rabbitmq_vhost: str | None = os.getenv("RABBITMQ_VHOST")

        self.postgresql_host: str | None = os.getenv("POSTGRESQL_HOST")
        self.postgresql_port: str | None = os.getenv("POSTGRESQL_PORT")
        self.postgresql_username: str | None = os.getenv("POSTGRESQL_USERNAME")
        self.postgresql_password: str | None = os.getenv("POSTGRESQL_PASSWORD")
        self.postgresql_database: str | None = os.getenv("POSTGRESQL_DATABASE")

        self.r = redis.Redis(host=self.redis_host, port=self.redis_port)

        self.worker_group: str | None = None
        self.worker_id: str | None = None

        self.app: Celery = Celery(
            "fio",
            broker=f"amqp://{self.rabbitmq_username}:{self.rabbitmq_password}"
            + f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}",
            backend="db+postgresql://"
            + f"{self.postgresql_username}:{self.postgresql_password}"
            + f"@{self.postgresql_host}/{self.postgresql_database}",
        )

    def register_worker(self, worker_group: str, worker_id: str) -> Self:
        self.worker_id = worker_id
        self.worker_group = worker_group

        self.r.sadd(self.worker_group, self.worker_id)

        print(f"Registered worker {self.worker_id} for group {self.worker_group}")

        return self

    def start_worker(self) -> None:
        if self.worker_id is None:
            raise ValueError("worker_id must be set before starting the worker")
        self.app.worker_main(["worker", "--loglevel=info", "-E", "-Q", self.worker_id])

    def __del__(self) -> None:
        if self.worker_group is not None and self.worker_id is not None:
            print(
                f"Unregistering worker {self.worker_id} for group {self.worker_group}"
            )
            self.r.srem(f"workers_{self.worker_group}", self.worker_id)
        else:
            pass

    def get_workers(self, worker_group: str) -> set[Any]:
        return self.r.smembers(worker_group)  # type: ignore[return-value]


worker = Worker()
hostname: str = socket.gethostname()


@worker.app.task(name="celery_app.run_benchmark")
# def run_benchmark(filename: str, wave_id: str, timestamp: datetime.datetime) -> dict:
def run_benchmark() -> dict:
    raise NotImplementedError
    # TODO: Add worker id group@host
    # return {"status": "Passed", "test": [1, 2, 3, 4]}
