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
- The benchmarking tool must be fully containerized using Docker.
- Users should be able to pull the Docker image from a public Docker repository.
- The tool must include a Docker Compose file.
- The tool should provide a user-friendly interface for configuring and starting benchmarks.
- The tool should provide easy to understand output for the benchmarking results
- Users should be able to start the benchmarking tool with a single command.

Reliability:
- In case of a worker node failure, the benchmark coordination must continue for the other nodes.

Performance:
- The tool should not interfere with the FIO Benchmark

Security:
- The communication between the worker nodes and the coordinator must be encrypted.

## License
The project is licensed under MIT, see the LICENSE for more information.

## Acknowledgements
We would like to express our gratitude to the
[FIO Project](https://fio.readthedocs.io/en/latest/fio_doc.html) and its
contributors.
The tools and resources provided by the FIO Project have been indispensable to
the development of this tool.
