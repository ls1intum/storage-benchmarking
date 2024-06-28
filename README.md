# Benchmarking Tool
Benchmarking Tool using Flexible I/O Tester (FIO) to test performance of IO
operations in containerized environments.

## Requirements
### Functional
- The tool should gather a set of performance metrics
- The tool should allow to compare performance of different storage solutions
- The tool should ship with pre-defined job configs for common tests
  - The tool should include configs for different workloads (git, web server, video streams)
  - The tool should include configs for testing performance of different block sizes
- User must be able to provide a custom FIO config to run the benchmark.
- The coordinator node must distribute benchmark tasks to worker nodes.
- The results of the tasks must be aggregated, so they can be processed later.

### Non-Functional Requirements
Usability:
- The tool should provide a command line interface for configuring and starting benchmarks.
- The tool should provide simplified output for the single-run benchmarking results
- Users should be able to start the benchmarking tool with a single command.

Reliability:
- In case of a worker node failure, the benchmark coordination must continue for the other nodes.

Performance:
- The tool should not interfere with the FIO Benchmark

Security:
- The communication between the worker nodes and the coordinator must be encrypted.

Constraints:
- The benchmarking tool must be fully containerized using Docker.
- Users should be able to pull the Docker image from a public Docker repository.
- The tool must include a Docker Compose file.

## Usage

We provide the tool as a Docker image since we primarily intend to benchmark
performance on containerized environments. For guides on how to perform the
benchmarks on bare metal, check out the Installation section.

To run the tool in the container:
```sh
docker run --rm -it ghcr.io/ls1intum/storage-benchmarking
```

```
usage: main.py [-h] {run,worker,coordinator} ...

Benchmarking Cluster

positional arguments:
  {run,worker,coordinator}
                        Role of the execution
    run                 Single run options
    worker              Worker node options
    coordinator         Coordinator node options

options:
  -h, --help            show this help message and exit

Developed by Colin Wilk as part of his Bachelor Thesis. Licensed as MIT, see LICENSE file for details
```

You can perform a single benchmark using the run command
```sh
docker run --rm -it ghcr.io/ls1intum/storage-benchmarking run -d /tmp
```

```
Job                Duration in Seconds
-----------------  ---------------------
random-reads       10s
random-writes      10s
sequential-reads   10s
sequential-writes  10s
web-server-assets  25s
media-streaming    20s
TOTAL              85s
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Metric                           | random-reads     | random-writes   | sequential-reads   | sequential-writes   | web-server-assets   | media-streaming   |
+==================================+==================+=================+====================+=====================+=====================+===================+
| Total Read IO                    | 1.1 GiB          | 0 Bytes         | 5.0 GiB            | 0 Bytes             | 21.8 GiB            | 39.2 GiB          |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Total Write IO                   | 0 Bytes          | 9.7 GiB         | 0 Bytes            | 8.8 GiB             | 0 Bytes             | 0 Bytes           |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Read Bandwidth                   | 235.2 MiB/s      | 0 Bytes/s       | 1022.1 MiB/s       | 0 Bytes/s           | 1.5 GiB/s           | 3.9 GiB/s         |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Write Bandwidth                  | 0 Bytes/s        | 1.9 GiB/s       | 0 Bytes/s          | 1.8 GiB/s           | 0 Bytes/s           | 0 Bytes/s         |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Read IOPS                        | 60_205.56 IOPS   | 0.00 IOPS       | 261_660.87 IOPS    | 0.00 IOPS           | 381_679.89 IOPS     | 32_120.39 IOPS    |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Write IOPS                       | 0.00 IOPS        | 509_639.87 IOPS | 0.00 IOPS          | 460_674.47 IOPS     | 0.00 IOPS           | 0.00 IOPS         |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Read Submission Latency          | 0 microseconds   | 0 microseconds  | 0 microseconds     | 0 microseconds      | 12 microseconds     | 22 microseconds   |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Read Completion Latency          | 64 microseconds  | 0 microseconds  | 7 microseconds     | 0 microseconds      | 657 microseconds    | 1 millisecond     |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Read Total Latency               | 64 microseconds  | 0 microseconds  | 7 microseconds     | 0 microseconds      | 669 microseconds    | 1 millisecond     |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Write Submission Latency         | 0 microseconds   | 0 microseconds  | 0 microseconds     | 0 microseconds      | 0 microseconds      | 0 microseconds    |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Write Completion Latency         | 0 microseconds   | 2 microseconds  | 0 microseconds     | 2 microseconds      | 0 microseconds      | 0 microseconds    |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Write Total Latency              | 0 microseconds   | 2 microseconds  | 0 microseconds     | 2 microseconds      | 0 microseconds      | 0 microseconds    |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Job Runtime                      | 20 seconds       | 10 seconds      | 10 seconds         | 5 seconds           | 2 minutes           | 40 seconds        |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| User CPU                         | 3.19%            | 26.19%          | 10.22%             | 24.60%              | 12.67%              | 3.00%             |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| System CPU                       | 14.48%           | 72.41%          | 36.39%             | 74.22%              | 37.45%              | 16.50%            |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Context Switches                 | 303,094          | 868             | 28,193             | 601                 | 155,691             | 107,834           |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Read Latency (99.0 Percentiles)  | 94 microseconds  | ---             | 206 microseconds   | ---                 | 4 milliseconds      | 6 milliseconds    |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Read Latency (99.9 Percentiles)  | 123 microseconds | ---             | 465 microseconds   | ---                 | 8 milliseconds      | 9 milliseconds    |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Write Latency (99.0 Percentiles) | ---              | 5 microseconds  | ---                | 3 microseconds      | ---                 | ---               |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
| Write Latency (99.9 Percentiles) | ---              | 24 microseconds | ---                | 15 microseconds     | ---                 | ---               |
+----------------------------------+------------------+-----------------+--------------------+---------------------+---------------------+-------------------+
```

You can run any of the shipped `job_files` from fio, such as block size tests:
```sh
docker run --rm -it ghcr.io/ls1intum/storage-benchmarking run -d /tmp -c /app/job_files/blocks.ini
```

Naturally you can mount your own custom ini file into the container and run
that:
```sh
docker run --rm -it -v /my-conf.ini:$(pwd)/my-conf.ini ghcr.io/ls1intum/storage-benchmarking run -d /tmp -c /my-conf.ini
```

## Installation
To run the project locally clone it first:
```sh
git clone https://github.com/ls1intum/storage-benchmarking
cd storage-benchmarking
```

Then install the dependencies using [Poetry](https://python-poetry.org/)
(you can install poetry with pip: `pip install poetry`).
```sh
poetry install --no-dev
```

Make sure you have fio installed and in your `PATH`;
```sh
$ fio -v
fio-3.37
```

Then you can run the project as described in the Usage section with
```sh
poetry run python3 src/benchmarking_tool/main.py
```

## License
The project is licensed under MIT, see the LICENSE for more information.

## Acknowledgements
We would like to express our gratitude to the
[FIO Project](https://fio.readthedocs.io/en/latest/fio_doc.html) and its
contributors.
The tools and resources provided by the FIO Project have been indispensable to
the development of this tool.
