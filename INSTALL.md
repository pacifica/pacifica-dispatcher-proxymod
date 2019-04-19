# Pacifica Dispatcher for proxymod

## Installation Guide

### Prerequisites

Please ensure that the following prerequisites are installed.

* [Docker](https://www.docker.com)

* [Git](https://git-scm.com)

* [Python (version 3)](https://www.python.org/)

### Step-by-step Instructions

**Note: The following instructions are given in [Bash](https://www.gnu.org/software/bash/) shell script syntax and are suitable for macOS and Unix operating systems.**

1. Open a new terminal.

2. Clone the Git repository:

```bash
git clone https://github.com/pacifica/pacifica-dispatcher-proxymod.git
```

3. Change directory to the cloned Git repository:

```bash
cd pacifica-dispatcher-proxymod
```

4. Create a new Python virtual environment in the `env` subdirectory:

```bash
python3 -m venv env
```

5. Update the Python package manager (within the context of the virtual environment):

```bash
env/bin/pip3 install --upgrade pip
```

6. Install the contents of the Git repository (within the context of the virtual environment):

```bash
env/bin/pip3 install -e .
```

## Testing Guide

### Step-by-step instructions

**Note: The following instructions are given in [Bash](https://www.gnu.org/software/bash/) shell script syntax and are suitable for macOS and Unix operating systems.**

1. Open a new terminal.

2. Change directory to the cloned Git repository.

3. Change directory to the `tests` subdirectory:

```bash
cd tests
```

4. Run the test suite (within the context of the virtual environment):

```bash
env/bin/python3 -m unittest proxymod_test.py
```

## Start-up Guide

### Step-by-step instructions

**Note: The following instructions are given in [Bash](https://www.gnu.org/software/bash/) shell script syntax and are suitable for macOS and Unix operating systems.**

1. Open a new terminal.

2. Change directory to the cloned Git repository.

3. Start [RabbitMQ](https://www.rabbitmq.com/) using Docker:

```bash
docker-compose up rabbit
```

4. Open a new terminal.

5. Change directory to the cloned Git repository.

6. Start [Celery](http://www.celeryproject.org/) (within the context of the virtual environment):

```bash
env DATABASE_URL="sqliteext:///db.sqlite3" env/bin/celery -A "pacifica.dispatcher_proxymod.__main__:celery_app" worker -l info
```

7. Open a new terminal.

8. Change directory to the cloned Git repository.

9. Start the Web server (within the context of the virtual environment):

```bash
env DATABASE_URL="sqliteext:///db.sqlite3" env/bin/python3 -m "pacifica.dispatcher_proxymod.__main__"
```

10. The Web server is now running at http://127.0.0.1:8069/.

## Subscription Guide

Subscriptions to the Pacifica notifications service require a notifications URL and may contain some authentication.
Discuss with the Systems Administrator of your Pacifica installation about authenticating to the notifications service.

The service description is located
[here](https://github.com/pacifica/pacifica-notifications/blob/master/docs/exampleusage.md#subscriptions)
and we will dig further into specifics for this dispatcher.

```bash
JSONPATH=$(cat pacifica/dispatcher_proxymod/jsonpath2/proxymod.txt)
curl -X POST -H 'Content-Type: application/json' -u user:password http://notify.example.com/eventmatch -d'{
    "name": "ProxyMod Event Match",
    "jsonpath": "'${JSONPATH}'",
    "target_url": "http://mylaptop.example.com:8069/receive"
}'
```

## Upload Guide

To start the process an initial upload needs to be executed. The data and uploader configuration is located in
the `tests` directory.

 1. Install the Pacifica CLI.
```bash
env/bin/pip3 install pacifica-cli
```
 2. Change working directory to `tests`.
```bash
cd tests/test_files/C234-1234-1234/data
```
 3. Configure the CLI (you will need input from your Systems Administrator for the values here).
```bash
pacifica-cli configure
```
 4. Perform the upload and add the additional project information.
```bash
pacifica-cli upload --project XXXX
```
