"""
Benchmarking Cluster Command-Line Interface

This Python module provides a command-line interface (CLI) for running
storage benchmarks using FIO (Flexible I/O Tester). The CLI allows users
to perform benchmarks directly or to execute worker and coordinator nodes
to facilitate distributed and automated benchmarks across a cluster.

Features:
- **Run Single Benchmarks:** Execute an FIO benchmark on a specified directory,
  with options to provide a custom configuration file.
- **Worker Node:** Register a worker node with a specified group, which can
  be managed by a coordinator to perform distributed benchmarks.
- **Coordinator Node:** Coordinate multiple worker nodes across different
  groups to execute distributed benchmark tasks.

Arguments:
- **role:** Specifies the role of the execution (run, worker, or coordinator).

### Run Role
Executes a single FIO benchmark.
- `-d`/`--directory` (str, required): Directory on which to perform the benchmark.
- `-c`/`--config` (str, optional): Path to a custom configuration file.

### Worker Role
Registers and starts a worker node.
- `--hostname` (str, optional): Overwrite node's hostname.
- `-g`/`--group` (str, required): Set worker group.

### Coordinator Role
Coordinates worker nodes to perform distributed benchmarks.
- `-g`/`--groups` (str, required): Groups of workers to trigger sequentially.
- `-f`/`--filenames` (str, required): Filenames of the FIO benchmark jobs,
  located in the job_files folder of the workers.

Usage:
To run this script, use the following command-line arguments:

```sh
# Single benchmark run
python script_name.py run -d /path/to/directory -c /path/to/config

# Register worker node
python script_name.py worker -g worker_group --hostname custom_hostname

# Coordinate benchmarks across worker nodes
python script_name.py coordinator -g group1 group2 -f benchmark.job
"""

import argparse
import os
import sys

# Add module to path as long as main entrypoint is not outside of modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarking_tool.celery_app import hostname, worker
from benchmarking_tool.coordinator import Coordinator
from benchmarking_tool.fio import Fio, FioConfig, FioResult

parser = argparse.ArgumentParser(
    description="Benchmarking Cluster",
    epilog="Developed by Colin Wilk as part of his Bachelor Thesis. "
    + "Licensed as MIT, see LICENSE file for details",
)
subparsers = parser.add_subparsers(dest="role", help="Role of the execution")

################################################################################
# Run Parameters
################################################################################
parser_run: argparse.ArgumentParser = subparsers.add_parser(
    "run", help="Single run options"
)
parser_run.add_argument(
    "-d",
    "--directory",
    help="Selects the directory that is to perform the benchmark on",
    type=str,
    required=True,
)
parser_run.add_argument(
    "-c",
    "--config",
    help="Provide Custom Configuration file to run",
    type=str,
    required=False,
    default=None,
)
parser_run.add_argument(
    "--print-report", help="Prints the report JSON to stdout", action="store_true"
)
parser_run.add_argument(
    "--export",
    help="Export the report JSON to a file",
    type=str,
    required=False,
    default="",
)

################################################################################
# Worker Parameters
################################################################################
parser_worker: argparse.ArgumentParser = subparsers.add_parser(
    "worker", help="Worker node options"
)
parser_worker.add_argument(
    "--hostname",
    help="Overwrite node hostname",
    default=None,
    type=str,
)
parser_worker.add_argument(
    "-g",
    "--group",
    help="Set worker group",
    required=True,
    type=str,
)
parser_worker.add_argument(
    "-d",
    "--directory",
    help="Selects the directory that is to perform the benchmark on",
    type=str,
    required=True,
)

################################################################################
# Coordinator Parameters
################################################################################
parser_coordinator: argparse.ArgumentParser = subparsers.add_parser(
    "coordinator", help="Coordinator node options"
)
parser_coordinator.add_argument(
    "-g",
    "--groups",
    help="Groups of workers that should be triggered in the order they are defined",
    nargs="+",
    type=str,
    required=True,
)
parser_coordinator.add_argument(
    "-f",
    "--filenames",
    help="Filenames of the fio benchmark job. "
    + "Must be defined in the job_files folder of the workers",
    nargs="+",
    type=str,
    required=True,
)
parser_coordinator.add_argument(
    "-t",
    "--trigger",
    help="Trigger a Job immediately and then exit. Useful for testing",
    action="store_true",
)
parser_coordinator.add_argument(
    "--random",
    help="Chooses a node from the group at random instead of running on all nodes",
    action="store_true",
)
parser_coordinator.add_argument(
    "--quick",
    help="Schedule next benchmark directly after the previous one finished",
    action="store_true",
)
parser_coordinator.add_argument(
    "--runs",
    help="Number of runs to make (used with the quick option)",
    type=int,
    required=False,
    default=0,
)

if __name__ == "__main__":
    args = parser.parse_args()
    if args.role is None:
        parser.print_help()

    if args.role == "run":
        fio = Fio()
        config_str: str = args.config or "job_files/default.ini"
        config: FioConfig = FioConfig(config_str).print_job_runtime()
        res: FioResult = fio.run(config, args.directory).print_table()
        if args.print_report:
            print(res.get_json())
        if args.export != "":
            res.export_json(args.export)

    if args.role == "worker":
        if args.hostname is None:
            args.hostname = hostname
        worker.register_worker(args.group, args.hostname, args.directory).start_worker()

    if args.role == "coordinator":
        coordinator = (
            Coordinator().set_worker_groups(args.groups).set_filenames(args.filenames)
        )
        if args.trigger:
            coordinator.trigger_benchmark(args.random)

        else:
            coordinator.run(args.random, args.quick)
