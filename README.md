# zPod Core

zPodFactory Core Engine

## DEVELOPMENT ENVIRONMENT SETUP

Complete the following steps to set up your development environment:

1. Install Docker and Docker Compose

1. Install pyenv

    ```bash
    brew install pyenv
    ```

1. Install Poetry:

    ```bash
    pip install poetry
    ```

1. Configure Virtual Environment.  In the `/zpodapi` directory, run:

    ```bash
    pyenv install 3.10.7
    pyenv local 3.10.7
    poetry config virtualenvs.in-project true
    poetry install
    ```

1. Configure Environment Variables.  (See `/zpodapi/src/zpodapi/lib/settings.py` file for all available settings)  In the root directory, run:

    ```bash
    cp .env.default .env
    vim .env
    ```

1. For Visual Studios Code, do the following:

    a. Configure the zpodcore.code-workspace.  In `/` run:

    ```bash
    cp zpodcore.code-workspace.default zpodcore.code-workspace
    ```

    Make sure that the port variable in launch.configurations.connect.port matches the port stored in the `ZPODAPI_DEBUG_HOSTPORT` environment variable.

1. Build the Docker containers.  (For DEV, make sure that the `COMPOSE_FILE` environment variable is set to `docker-compose.dev.yml`.  In the root directory, run:

    ```bash
    docker compose build
    ```

1. Start the environment.  In the root directory, run:

    ```bash
    docker compose up
    ```

1. Verify that zpodapi is working by opening a browser and going to `http://localhost:[8000 or ZPODAPI_HOSTPORT]` and `http://localhost:[8000 or ZPODAPI_HOSTPORT]/docs`

1. Build zpodengine container and create Blocks and Deployments

    ```bash
    just zpodengine-init
    ```
