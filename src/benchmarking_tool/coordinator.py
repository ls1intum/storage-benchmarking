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
        last_wave_id (str | None): Stores the last benchmark wave ID.
        worker_groups (list[str]): List of worker groups.
        filename (str): Filename to be used in benchmarking tasks.

    Methods:
        __schedule_every_2_hours() -> None:
            Schedules the job to run every 2 hours starting at 00:00, 02:00, etc.

        get_results_from_wave_id(wave_id: str) -> dict:
            Retrieves results of the benchmark associated with given wave ID.

        __log_progress() -> None:
            Logs the progress of the current benchmark run.

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

    # Schedule the job to run every 2 hours starting at 00:00, 02:00, 04:00, etc.
    # FIXME: Way to configure this over CLI
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

    def get_results_from_wave_id(self, wave_id: str) -> dict:
        raise NotImplementedError

    def __log_progress(self) -> None:
        # results = self.get_results_from_wave_id(self.last_wave_id)
        raise NotImplementedError

    def __init__(self) -> None:
        self.last_wave_id: str | None = None

    def trigger_benchmark(self) -> None:
        trigger_time: datetime.datetime = datetime.datetime.now()
        wave_id: str = str(uuid.uuid4())
        l.info("Triggering Benchmark")
        self.__log_progress()
        self.last_wave_id = wave_id
        groups: list = []
        for worker_group in self.worker_groups:
            workers: set[Any] = worker.get_workers(worker_group)
            grouped_tasks = group(
                run_benchmark.s(
                    filename=self.filename, wave_id=wave_id, timestamp=trigger_time
                ).set(queue=worker.decode())
                for worker in workers
            )
            groups.append(grouped_tasks)

        chained_tasks = chain(*groups)
        chained_tasks.apply_async()

    def run(self) -> NoReturn:
        self.__schedule_every_2_hours()
        while True:
            schedule.run_pending()
            time.sleep(1)

    def set_worker_groups(self, worker_groups: list[str]) -> Self:
        self.worker_groups: list[str] = worker_groups
        return self

    def get_worker_groups(self) -> list[str]:
        return self.worker_groups

    def set_filename(self, filename: str) -> Self:
        self.filename: str = filename
        return self

    def get_filename(self) -> str:
        return self.filename


if __name__ == "__main__":
    Coordinator().set_worker_groups(["Worker_A", "Worker_B"]).set_filename(
        "full_benchmark"
    ).run()