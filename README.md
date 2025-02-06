# EHservice Microservices Quick Start

This is a simple RabbitMQ-based microservices architecture showcasing:
- A **Controller** microservice
- An **Entitlement** (Auth) microservice
- A **Data** microservice

Each service communicates via RabbitMQ queues defined in `config.py`.

## Prerequisites

1. **Docker** Desktop or Docker Engine (for running RabbitMQ in a container)
2. **Python 3.9+** (with `venv` module available)

## Setup & Run

1. **Clone** this repo and open a terminal in the project folder (`EHservice`).

2. **Launch Services**:
   ```powershell
   # In PowerShell:
   .\start_services.ps1
This script will:
Check if Docker is running
Start or run RabbitMQ in a Docker container (exposing ports 5672 and 15672)
Create/activate a virtual environment (venv) and install requirements.txt
Open 3 new PowerShell windows for each microservice: controller, entitlement, data
Test the flow by sending example messages to the frontdoor queue:

powershell
Copy
Edit
python .\test_frontdoor_publisher.py
You’ll see logs appear in each microservice window.

Access RabbitMQ Management UI:

Go to http://localhost:15672
Default credentials: guest / guest
Check the queues, messages, etc.
Stopping & Cleaning Up
Stop the Microservices: Simply close each PowerShell window or press Ctrl+C.
Stop the RabbitMQ Container:
powershell
Copy
Edit
docker stop rabbitmq
Or remove it entirely:

docker rm -f rabbitmq

Project Structure
config.py - Central queue definitions
auth_utils.py - Token/role logic
controller.py, entitlement_service.py, data_service.py - Main microservices
test_frontdoor_publisher.py - Sends sample requests to frontdoor
start_services.ps1 - Script to start RabbitMQ & all services quickly
requirements.txt - Python dependencies (e.g. pika)
Moving to a Remote Server
Install Docker and Python on the remote machine
Copy these files or clone the repo
Run start_services.ps1 in a Windows environment (or adapt for Linux with a Bash script)
If you want services to run in the background, consider nohup (on Linux) or scheduled tasks / service wrappers on Windows.

---

## 5. **Running on a Remote Server**

1. **Install Docker** & **Python** on the target server.  
2. Copy the entire `EHservice` folder to the server.  
3. Run `start_services.ps1` (Windows) or adapt it for a shell script on Linux.  
4. Ensure any firewall ports (5672, 15672) are open if you need external access.

---

### **That’s It!**

With this setup:

- You can quickly spin up RabbitMQ in Docker.  
- Each microservice runs in a separate terminal (making it easy to watch logs).  
- The `test_frontdoor_publisher.py` can push example messages for end-to-end testing.  
- A single command (`.\start_services.ps1`) sets it all up from a fresh clone.
