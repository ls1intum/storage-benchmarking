"""
FIO - Flexible I/O Tester
~~~~~~~~~~~~~~~~~~~~~~~~~

This module provides a set of classes to facilitate benchmarking using FIO.
It includes functionalities to configure FIO, run benchmarks, and process the
results.

Imports:
    configparser: Parses configuration files.
    json: Provides JSON parsing and serialization.
    os: Provides a way of using operating system dependent functionality.
    subprocess: Allows spawning new processes and connecting to their
                input/output/error pipes.
    tempfile: Generates temporary files and directories.
    datetime: Supplies classes for manipulating dates and times.
    typing: Provides various tools for type hinting.
    humanize: Provides human-readable representations of numbers and times.
    tabulate: Pretty-print tabular data.

Classes:
    FioResult: Processes and presents FIO benchmark results.
    FioConfig: Handles and parses FIO configuration files.
    Fio: Executes FIO benchmarks.

:copyright (c) 2024 Colin Wilk.
:license: MIT, see LICENSE for more details.
"""

import configparser
import json
import os
import subprocess
import tempfile
from datetime import timedelta
from typing import IO, Any, Self

import humanize
from tabulate import tabulate


class FioResult:
    """
    Class to process and present FIO benchmark results.

    Attributes:
        NO_RESULT_STRING (str): String representation for unavailable results.
        result (dict): The FIO benchmark result.
    """

    NO_RESULT_STRING = "---"

    def __init__(self, result: dict[Any, Any]) -> None:
        """
        Initialize the FioResult with the given result dictionary received from
        the FIO.run() method.

        Args:
            result (dict): The raw FIO result.
        """
        self.result: dict[Any, Any] = result

    @staticmethod
    def __humanize_bytes(value: Any) -> str:
        """
        Convert a byte value to a human-readable string.

        Args:
            value: The byte value to convert.

        Returns:
            str: Human-readable string representation of the byte value.
        """
        return (
            humanize.naturalsize(value, binary=True)
            if isinstance(value, int)
            else FioResult.NO_RESULT_STRING
        )

    @staticmethod
    def __humanize_time_ns(value: Any) -> str:
        """
        Convert a time value in nanoseconds to a human-readable string.

        Args:
            value: The time value in nanoseconds.

        Returns:
            str: Human-readable string representation of the time value.
        """
        return (
            humanize.naturaldelta(
                timedelta(microseconds=value / 1000), minimum_unit="microseconds"
            )
            if isinstance(value, (int, float))
            else FioResult.NO_RESULT_STRING
        )

    @staticmethod
    def safe_get(
        d: dict[Any, Any], keys: list[str], default: str | float | int = "---"
    ) -> Any:
        """
        Safely retrieve a value from a nested dictionary using a list of keys.

        Args:
            d (dict): The dictionary to fetch the value from.
            keys (list[str]): The list of keys for nested lookup.
            default: The default value to return if any key is not found.

        Returns:
            The retrieved value or default if any key is not found.
        """
        for key in keys:
            d: Any = d.get(key, None)  # type: ignore[no-redef]
            if d is None:
                return default
        return d

    @staticmethod
    def get_relevant_metrics(job: dict[Any, Any]) -> dict[str, str]:
        """
        Extract and convert relevant metrics from a FIO job dictionary to a more
        readable format. This is the method that decides what will be printed in
        summary methods of this class. If you want to add more relevant metrics
        you only need to do it here.

        Args:
            job (dict): The FIO job dictionary.

        Returns:
            dict[str, str]: A dictionary of relevant metrics in a human-readable
                            format.
        """
        # pylint: disable=line-too-long
        # fmt: off
        return {
            "Total Read IO":                    FioResult.__humanize_bytes(FioResult.safe_get(job, ["read", "io_bytes"])),
            "Total Write IO":                   FioResult.__humanize_bytes(FioResult.safe_get(job, ["write", "io_bytes"])),
            "Read Bandwidth":                   FioResult.__humanize_bytes(FioResult.safe_get(job, ["read", "bw_bytes"])) + "/s",
            "Write Bandwidth":                  FioResult.__humanize_bytes(FioResult.safe_get(job, ["write", "bw_bytes"])) + "/s",
            "Read IOPS":                        f"{FioResult.safe_get(job, ['read', 'iops'], 0.0):_.2f} IOPS",
            "Write IOPS":                       f"{FioResult.safe_get(job, ['write', 'iops'], 0.0):_.2f} IOPS",
            "Read Submission Latency":          FioResult.__humanize_time_ns(FioResult.safe_get(job, ["read", "slat_ns", "mean"])),
            "Read Completion Latency":          FioResult.__humanize_time_ns(FioResult.safe_get(job, ["read", "clat_ns", "mean"])),
            "Read Total Latency":               FioResult.__humanize_time_ns(FioResult.safe_get(job, ["read", "lat_ns", "mean"])),
            "Write Submission Latency":         FioResult.__humanize_time_ns(FioResult.safe_get(job, ["write", "slat_ns", "mean"])),
            "Write Completion Latency":         FioResult.__humanize_time_ns(FioResult.safe_get(job, ["write", "clat_ns", "mean"])),
            "Write Total Latency":              FioResult.__humanize_time_ns(FioResult.safe_get(job, ["write", "lat_ns", "mean"])),
            "Job Runtime":                      humanize.precisedelta(FioResult.safe_get(job, ["job_runtime"], 0) / 1000),
            "User CPU":                         f"{FioResult.safe_get(job, ['usr_cpu'], 0.0):.2f}%",
            "System CPU":                       f"{FioResult.safe_get(job, ['sys_cpu'], 0.0):.2f}%",
            "Context Switches":                 humanize.intcomma(FioResult.safe_get(job, ["ctx"], 0)),
            "Read Latency (99.0 Percentiles)":  FioResult.__humanize_time_ns(FioResult.safe_get(job, ["read", "clat_ns", "percentile", "99.000000"])),
            "Read Latency (99.9 Percentiles)":  FioResult.__humanize_time_ns(FioResult.safe_get(job, ["read", "clat_ns", "percentile", "99.900000"])),
            "Write Latency (99.0 Percentiles)": FioResult.__humanize_time_ns(FioResult.safe_get(job, ["write", "clat_ns", "percentile", "99.000000"])),
            "Write Latency (99.9 Percentiles)": FioResult.__humanize_time_ns(FioResult.safe_get(job, ["write", "clat_ns", "percentile", "99.900000"])),
        }
        # fmt: on

    def get_jobs(self) -> list[dict[Any, Any]]:
        """
        Get the list of jobs from the FIO result.

        Returns:
            list[dict]: List of job dictionaries.
        """
        return self.result["jobs"]

    def get_jobnames(self) -> list[str]:
        """
        Get only the names of all jobs in the FIO result.

        Returns:
            list[str]: List of job names.
        """
        return list(map(lambda x: x["jobname"], self.result["jobs"]))

    def get_job(self, job: str) -> dict[Any, Any]:
        """
        Retrieve details of a specific job by its name.

        Args:
            job (str): The name of the job.

        Returns:
            dict: The job details.

        Raises:
            ValueError: If the job name is not found in the result.
        """
        for entry in self.result["jobs"]:
            if entry["jobname"] == job:
                return entry
        raise ValueError(f"Could not find job {job} in result")

    def print_table(self) -> Self:
        """
        Print the relevant metrics of all jobs in a tabular format.
        The values printed here are defined in the get_relevant_metrics method.

        The printed table looks like this:

        +----------------------------------+----------+--------+
        | Metric                           | job1    | job2    |
        +==================================+=========+=========+
        | Metric 1                         |         |         |
        +----------------------------------+---------+---------+
        | Metric 2                         | Value 1 | Value 2 |
        +----------------------------------+---------+---------+
        | ...                              | ...     | ...     |
        +----------------------------------+---------+---------+

        Returns:
            Self: The current instance for method chaining.
        """
        table: list[list[str]] = []
        headers: list[str] = ["Metric"] + self.get_jobnames()
        jobs: list[dict[Any, Any]] = [
            self.get_relevant_metrics(job) for job in self.get_jobs()
        ]

        for k, _ in self.get_relevant_metrics(self.get_jobs()[0]).items():
            row: list[str] = [k]
            for job in jobs:
                row.append(job[k])
            table.append(row)

        print(tabulate(table, headers=headers, tablefmt="grid"))
        return self

    def export_json(self, path: str) -> Self:
        """
        Export the FIO result to a JSON file.

        Args:
            path (str): The path to save the JSON file.

        Returns:
            Self: The current instance for method chaining.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.result, f)
        return self

    def get_json(self) -> str:
        """
        Export the FIO result as a JSON string.

        Returns:
            str: JSON string of the report
        """
        return json.dumps(self.result)


class FioConfig:
    """
    Class to handle and parse FIO configuration files.

    Attributes:
        config (ConfigParser): The ConfigParser instance for reading the
                               configuration.
        config_file (str): The path to the configuration file.
    """

    def __parse_config(self) -> None:
        """
        Parse the FIO configuration file using ConfigParser.
        """
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config.optionxform = str  # type: ignore
        with self.get_fd() as f:
            self.config.read_file(f)

    def __init__(self, config_file: str) -> None:
        """
        Initialize the FioConfig with the given configuration file.

        Args:
            config_file (str): The path to the configuration file.
        """
        self.config_file: str = config_file
        self.__parse_config()

    def get_fd(self, mode: str = "r") -> IO[Any]:
        """
        Get a file descriptor for the configuration file.

        Args:
            mode (str): The file mode for opening the file.

        Returns:
            IO[Any]: The file descriptor.
        """
        return open(self.config_file, mode, encoding="utf-8")

    def get_contents(self) -> str:
        """
        Get the contents of the configuration file as a string.

        Returns:
            str: The configuration file contents.
        """
        with open(self.config_file, "r", encoding="utf-8") as f:
            return f.read()

    def get_sections(self) -> list[str]:
        """
        Get all sections in the configuration file except the 'global' section.

        Returns:
            list[str]: List of section names.
        """
        return [section for section in self.config.sections() if section != "global"]

    def get_globals(self) -> list[tuple[str, str]]:
        """
        Get all items in the 'global' section of the configuration file.

        Returns:
            list[tuple[str]]: List of (key, value) pairs in the 'global'
                              section.
        """
        return self.get_section("global")

    def get_section(self, section: str) -> list[tuple[str, str]]:
        """
        Get all items in a specific section of the configuration file.

        Args:
            section (str): The section name.

        Returns:
            list[tuple[str]]: List of (key, value) pairs in the section.
        """
        return self.config.items(section)

    @staticmethod
    def search_tuple_list(arr: list[tuple[str, str]], key: str) -> str | None:
        """
        Search for a key in a list of tuples and return its value.

        Args:
            arr (list[tuple[str]]): The list of (key, value) tuples.
            key (str): The key to search for.

        Returns:
            str | None: The value associated with the key, or None if not found.
        """
        for tup in arr:
            if tup[0] == key:
                return tup[1]
        return None

    def get_config_value(self, section: str, key: str) -> str | None:
        """
        Get a configuration value from a specific section or the 'global'
        section.

        Args:
            section (str): The section name.
            key (str): The key to search for.

        Returns:
            str | None: The configuration value or None if not found.
        """
        job_value: str | None = FioConfig.search_tuple_list(
            self.get_section(section), key
        )
        global_value: str | None = FioConfig.search_tuple_list(self.get_globals(), key)
        return job_value if job_value is not None else global_value

    def get_job_runtime(self) -> dict[str, int]:
        """
        Get the runtime for each job in seconds.

        Returns:
            dict[str, int]: Dictionary mapping job names to their runtime in
                            seconds.
        """
        runtime: dict[str, int] = {}
        for section in self.get_sections():
            runtime[section] = int(
                self.get_config_value(section, "ramp_time") or 0
            ) + int(self.get_config_value(section, "runtime") or 0)
        return runtime

    def print_job_runtime(self) -> Self:
        """
        Print the runtime for each job and the total runtime.

        Prints a table like this:

        Job    Duration in Seconds
        -----  ---------------------
        job 1  10s
        job 2  10s
        job 3  20s
        TOTAL  40s

        Returns:
            Self: The current instance for method chaining.
        """
        headers: list[str] = ["Job", "Duration in Seconds"]
        table: list[list[str]] = [
            [k, str(v) + "s"] for k, v in self.get_job_runtime().items()
        ]
        table.append(["TOTAL", str(sum(self.get_job_runtime().values())) + "s"])
        print(tabulate(table, headers=headers, tablefmt="simple"))
        return self


class Fio:
    """
    Class to handle FIO benchmark execution.

    Attributes:
        CONFIG_NAME (str): Default name for the FIO configuration file.
        RESULT_FILE (str): Default name for the FIO result file.
        temp_dir (TemporaryDirectory): Temporary directory for storing
                                       configuration files.
    """

    CONFIG_NAME = "fio.ini"
    RESULT_FILE = "result.json"

    def __dump_conf(self, config: FioConfig) -> str:
        """
        Dump the FIO configuration to a temporary file.

        Args:
            config (FioConfig): The FIO configuration object.

        Returns:
            str: The path to the temporary configuration file.
        """
        config_file: str = os.path.join(self.temp_dir.name, self.CONFIG_NAME)
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config.get_contents())
        return config_file

    @staticmethod
    def __exec_fio(
        config_file: str, directory: str
    ) -> subprocess.CompletedProcess[str]:
        """
        Execute the FIO benchmark and capture the result.

        Args:
            config_file (str): The path to the FIO configuration file.
            directory (str): The directory to run the benchmark in.

        Returns:
            subprocess.CompletedProcess[bytes]: The completed process containing
                                                the result.
        """
        return subprocess.run(
            ["fio", "--output-format=json", "--directory", directory, config_file],
            capture_output=True,
            text=True,
            check=False,
        )

    def __init__(self) -> None:
        """
        Initialize the Fio object and create a temporary directory.
        """
        self.temp_dir = tempfile.TemporaryDirectory()

    def __del__(self) -> None:
        """
        Cleanup the temporary directory.
        """
        self.temp_dir.cleanup()

    def run(self, config: FioConfig, data_mount: str) -> FioResult:
        """
        Run the FIO benchmark with the given configuration and data mount point.

        Args:
            config (FioConfig): The FIO configuration object.
            data_mount (str): The directory to run the benchmark in.

        Returns:
            FioResult: The result of the FIO benchmark.

        Raises:
            subprocess.CalledProcessError: If FIO returns a non-zero exit code.
        """
        config_file: str = self.__dump_conf(config)
        p: subprocess.CompletedProcess[str] = self.__exec_fio(config_file, data_mount)
        if p.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=p.returncode, cmd=p.args, output=p.stdout, stderr=p.stderr
            )
        return FioResult(json.loads(p.stdout))
