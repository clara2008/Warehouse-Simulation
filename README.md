# Docker Warehouse Simulation

This project provides the source code for a car seat warehouse simulation.
It is based on Docker container technology and serves as a cybersecurity testbed using the Wazuh SIEM platform.
Each simulation container is individually monitored by a Wazuh agent.

## Contents

* Dockerfiles and Python files for the simulation components
* YAML configuration files
* Wazuh single-node setup + configuration files
* Files for database deployment

## Requirements

* Docker
* Docker Compose
* PostgreSQL

## Installation

1. Before installing the project, a PostgreSQL database needs to be deployed, ideally as a Docker container. The demand below (retrieved from https://dev.to/andre347/how-to-easily-create-a-postgres-database-in-docker-4moj) can be used. An SQL script for creating the required tables is provided. There is also a dump file for the *warehouse* table. Make sure that all values in the *seat_id* and *status* columns are set to NULL. The *dos_table* can be filled with random values.
```
docker run --name postgres-db -e POSTGRES_PASSWORD=docker -p 5432:5432 -d postgres
```

3. Download this repository and use the following command.
```
docker-compose up
```

4. The containers should now be running. If not, this may be due to connection errors between the server and the remaining components. Restarting the stopped containers should solve this issue.

The login data for the Wazuh dashboard:
* user: admin
* password: SecretPassword
