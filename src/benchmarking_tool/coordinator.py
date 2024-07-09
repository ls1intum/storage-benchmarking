"""
Module to configure and run a benchmark Coordinator with Celery workers.

This module sets up a Coordinator class that schedules and triggers benchmarking
tasks executed by a group of Celery workers. The Coordinator manages job
scheduling of Celery workers.

Imports:
    datetime: Supplies classes for manipulating dates and times.
    time: Provides various time-related functions.
    uuid: Generates unique IDs.
    typing: Provides various tools for type hinting.
    schedule: Manages scheduling for periodic tasks.
    celery: An asynchronous task queue/job queue based on distributed message passing.
    loguru: A library for logging.
    celery_app: Module importing Celery app instance and tasks.
    worker: The Worker class managing Celery worker operations.

Classes:
    Coordinator: Orchestrates the scheduling, triggering, and management of
                 benchmark tasks using Celery workers.
"""

import datetime
import time
import uuid
from typing import Any, NoReturn, Self

import schedule
from celery import chain, group
from loguru import logger as l

from .celery_app import run_benchmark, worker


class Coordinator:
    """
    Orchestrates scheduling and triggering of benchmarking tasks using Celery
    workers.

    The Coordinator class schedules periodic tasks to run FIO benchmarks using a
    group of Celery workers. It manages the scheduling and task chaining of the
    benchmarks.

    Attributes:
        worker_groups (list[str]): List of worker groups.
        filename (str): Filename to be used in benchmarking tasks.

    Methods:
        __schedule_every_2_hours() -> None:
            Schedules the job to run every 2 hours starting at 00:00, 02:00, etc.

        trigger_benchmark() -> None:
            Triggers a new benchmark run and schedules tasks for Celery workers.

        run() -> NoReturn:
            Starts the coordinator to run scheduled tasks indefinitely.

        set_worker_groups(worker_groups: list[str]) -> Self:
            Sets the worker groups for the benchmark tasks.

        get_worker_groups() -> list[str]:
            Retrieves the list of worker groups.

        set_filename(filename: str) -> Self:
            Sets the filename to be used in benchmark tasks.

        get_filename() -> str:
            Retrieves the filename used in benchmark tasks.
    """

    def __schedule_every_2_hours(self) -> None:
        for t in [
            "00",
            "02",
            "04",
            "06",
            "08",
            "10",
            "12",
            "14",
            "16",
            "18",
            "20",
            "22",
        ]:
            schedule.every().day.at(f"{t}:00").do(self.trigger_benchmark)

    def __init__(self) -> None:
        pass

    def trigger_benchmark(self) -> None:
        trigger_time: datetime.datetime = datetime.datetime.now()
        wave_id: str = str(uuid.uuid4())
        l.info("Triggering Benchmark")
        groups: list = []
        for worker_group in self.worker_groups:
            for filename in self.filenames:
                workers: set[Any] = worker.get_workers(worker_group)
                grouped_tasks = group(
                    run_benchmark.s(
                        filename=filename, wave_id=wave_id, timestamp=trigger_time
                    ).set(queue=worker.decode())
                    for worker in workers
                )
                groups.append(grouped_tasks)

        chained_tasks = chain(*groups)
        chained_tasks.apply_async()

    def run(self) -> NoReturn:
        self.__schedule_every_2_hours()
        l.info("Coordinator Started")
        while True:
            schedule.run_pending()
            time.sleep(1)

    def set_worker_groups(self, worker_groups: list[str]) -> Self:
        self.worker_groups: list[str] = worker_groups
        return self

    def get_worker_groups(self) -> list[str]:
        return self.worker_groups

    def set_filenames(self, filenames: list[str]) -> Self:
        self.filenames: list[str] = filenames
        return self

    def get_filenames(self) -> list[str]:
        return self.filenames
