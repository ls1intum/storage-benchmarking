FROM python:3.11-bookworm

WORKDIR /app
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

COPY . /app

RUN pip3 install poetry
RUN poetry install --no-dev

RUN apt-get update && apt-get install -y fio

ENTRYPOINT ["poetry", "run", "python3", "src/benchmarking_tool/main.py"]
