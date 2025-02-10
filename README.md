```markdown
# EHservice Microservices Architecture

This project implements a microservices architecture using RabbitMQ as the sole inter-service communication channel. The services include:

- **RabbitMQ**: Messaging backbone (with management UI)
- **PostgreSQL**: Database for the data service
- **Entitlement Service**: Performs token/RBAC checks and routes messages
- **Controller Service**: Receives external requests via the `frontdoor` queue and forwards them for entitlement checking
- **Data Service**: The only service that interacts with the SQL database; it processes data requests and writes records

All services are containerized and orchestrated with Docker Compose. The only dependency between services is RabbitMQ. Each service is designed to operate independently.

---

## Project Structure

The project is organized as follows:

```
Folder PATH listing
|   .dockerignore
|   .gitignore
|   config.py
|   docker-compose.yml
|   README.md
|   requirements.txt
|   structure.txt
|   subscriber_frontdoor_output.py
|   test_pub.py
|   
+---controller
|       controller.py
|       Dockerfile
|       
+---data
|       data_service.py
|       Dockerfile
|       
+---entitlement
|       Dockerfile
|       entitlement_rules.json
|       entitlement_service.py
|       
\---__pycache__
        auth_utils.cpython-313.pyc
        config.cpython-312.pyc
        config.cpython-313.pyc
```

- **config.py**: Centralizes configuration values (queue names, RabbitMQ host, DATABASE_URL, etc.).
- **auth_utils.py**: Contains token decoding and role-based access logic.
- **Dockerfiles**: Each service has its own Dockerfile that copies the entire project so that shared modules (e.g., `config.py`, `auth_utils.py`) are available.

---

## Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Docker Compose](https://docs.docker.com/compose/)
- (For local testing of the publisher) Python 3.12 with dependencies from `requirements.txt` (or use the provided Docker command)

---

## Setup

1. **Clone the Repository**  
   Clone this repository to your local machine.

2. **Create a `.dockerignore` File**  
   (Ensure the following lines are present to exclude unnecessary files, such as your virtual environment.)

   ```dockerignore
   venv/
   __pycache__/
   *.pyc
   *.pyo
   *.pyd
   ```

3. **Build and Start the Services**  
   From the project root, run:

   ```bash
   docker-compose up --build
   ```

   This command will:
   - Build the Docker images for the controller, entitlement, and data services using the Dockerfiles provided in their respective directories.
   - Start the RabbitMQ and PostgreSQL containers.
   - Start all microservices, connecting them on the `ehservice_microservices` network.

4. **Access RabbitMQ Management UI**  
   Open your web browser and go to [http://localhost:15672](http://localhost:15672)
   - Default credentials: `guest` / `guest`

---

## Running the Test Publisher

Since you want to run the test publisher in a container (so you don’t need to install dependencies locally), use the following command in PowerShell from the project root:

```powershell
docker run --rm --network ehservice_microservices -v "$($PWD.Path):/app" -w /app -e RABBITMQ_HOST=rabbitmq python:3.12-slim bash -c "pip install -r requirements.txt && python test_pub.py"
```

### Explanation:
- `--rm`: Removes the container after it exits.
- `--network ehservice_microservices`: Attaches the container to the Docker Compose network so that the hostname `rabbitmq` resolves correctly.
- `-v "$($PWD.Path):/app"`: Mounts the current directory into `/app` in the container.
- `-w /app`: Sets `/app` as the working directory.
- `-e RABBITMQ_HOST=rabbitmq`: Sets the RabbitMQ host environment variable to `rabbitmq` (the service name).
- The command then installs dependencies and runs `test_pub.py`.

This command will send test messages to the `frontdoor` queue. You should see output from the publisher and then verify the message flow by checking:
- The logs of the controller, entitlement, and data services (using `docker-compose logs -f <service>`).
- The RabbitMQ management UI at [http://localhost:15672](http://localhost:15672).

---

## Viewing Logs

To view the logs of individual services, use the following commands:

- **Controller Service Logs:**
  ```bash
  docker-compose logs -f controller
  ```

- **Entitlement Service Logs:**
  ```bash
  docker-compose logs -f entitlement
  ```

- **Data Service Logs:**
  ```bash
  docker-compose logs -f data
  ```

- **RabbitMQ Logs:**
  ```bash
  docker-compose logs -f rabbitmq
  ```

---

## Stopping the Services

To stop and remove all containers, networks, and volumes created by Docker Compose, run:

```bash
docker-compose down
```

---

## Additional Notes

- **Microservice Independence:**  
  Only the data service connects to the PostgreSQL database. All other services communicate exclusively via RabbitMQ.

- **Environment Variables:**  
  Each service reads configuration (e.g., `RABBITMQ_HOST`, `DATABASE_URL`) from environment variables, making it easy to adjust settings for production.

- **Debugging:**  
  If any service fails to start, use `docker-compose logs -f <service>` to troubleshoot.

---

# Enjoy building your microservices with EHservice!
```
## Development Status

**Current stable version**:  
We've successfully implemented a microservices architecture with:
- **CRUD** operations in the data service
- **Entitlement** service with JSON-based RBAC rules
- **Controller** and **frontdoor** queues
- **RabbitMQ** for message routing
- **PostgreSQL** for persistence

**Branching for new features**:  
To add new features or experiment with changes, create a new branch from the current `main` (or use the `v1.0-crud-rbac` tag). For example:
```bash
git checkout main
git pull
git checkout -b new-feature

### Key Files and Directories

- **docker-compose.yml**: Defines services for RabbitMQ, PostgreSQL, controller, entitlement, and data.
- **controller/**:
  - `controller.py`: Handles frontdoor input, entitlement checks, data forwarding.
  - `Dockerfile`: Instructions for building the controller service.
- **entitlement/**:
  - `entitlement_service.py`: Reads JSON RBAC rules (`entitlement_rules.json`) and enforces them.
  - `entitlement_rules.json`: Defines read/write access for roles (green, blue, red).
  - `Dockerfile`: Instructions for building the entitlement service.
- **data/**:
  - `data_service.py`: Implements CRUD for animals/plants, plus logic for reading/writing records.
  - `Dockerfile`: Instructions for building the data service.
- **test_pub.py**: A test publisher script that sends various requests (GET/POST/PUT/DELETE) to `frontdoor`.
- **subscriber_frontdoor_output.py**: An optional subscriber script that listens on the `frontdoor_output` queue.

### Future ChatGPT Sessions

- Provide your README, `docker-compose.yml`, and relevant code snippets to ChatGPT so it understands the existing architecture.
- Reference the stable commit/tag (`v1.0-crud-rbac`) if you want ChatGPT to see the baseline state before new features are added.