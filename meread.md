# EHmicroService

EHmicroService is a microservices-based framework that demonstrates an event-driven architecture using RabbitMQ for messaging and PostgreSQL for data persistence. This project is an evolving starting point for a generic framework and is intended for future expansion and refinement.

## Architecture Overview

- **Microservices Components**:
  - **Controller Service**: Receives incoming API requests from the `frontdoor` RabbitMQ queue and routes them for further processing. It forwards requests to the entitlement check queue and, upon receiving a pass response, directs data-related requests to the Data Service.
  - **Entitlement Service**: Validates requests based on Role-Based Access Control (RBAC). Currently, it uses inline logic and a JSON-based rule set (from `entitlement_rules.json`) to determine access. In future iterations, this service will delegate to a dedicated AuthZ server for more robust authorization.
  - **Data Service**: Handles CRUD operations by interacting with a PostgreSQL database. It uses placeholder logic to map requests (e.g., categorizing "animals" to `table1` and "plants" to `table2`) and processes operations based on the HTTP method specified (GET, POST, PUT, DELETE). Future enhancements will introduce more sophisticated data mapping and error/response handling.

- **Messaging Flow**:
  1. A client publishes a message (including fields like `request_id`, `token`, `method`, and `item_type`) to the `frontdoor` queue.
  2. The **Controller Service** consumes the message and forwards it to the appropriate entitlement check queue.
  3. The **Entitlement Service**:
     - Decodes the provided token (using a now-deprecated `auth_utils` module) to determine the user role.
     - Applies inline RBAC checks (currently using hardcoded logic with reference to `entitlement_rules.json` for context) to decide if the request should pass.
     - For approved requests, it publishes the message to a designated “pass” queue (either for the Controller or Data Service). Rejected messages are sent to a `REJECTED` queue.
  4. For data-related requests, the **Data Service**:
     - Listens on its request queue, performs basic table mapping based on the `item_type`, and then proceeds with the database operation.
     - For GET requests, it queries the database and publishes the results to the `frontdoor_output` queue.
     - For POST, PUT, and DELETE operations, it currently executes the database operation without sending a detailed response back to the client.

- **Message Identification and Flow Tracking**:
  - Each message carries a `request_id` to enable tracing through the system’s logs. This ID is manually generated for now and serves as a placeholder for more advanced correlation mechanisms in the future.
  - The project uses RabbitMQ queues such as `frontdoor`, entitlement check queues (`CONTROLLER_ENTITLEMENT_CHECK` and `DATA_ENTITLEMENT_CHECK`), pass queues (`CONTROLLER_ENTITLEMENT_PASS` and `DATA_ENTITLEMENT_PASS`), and a response queue (`FRONTDOOR_OUTPUT`).

## Implementation Details

- **Configuration**:
  - A shared configuration module (`config.py`) defines environment variables and queue names, ensuring consistency across services.
  - Each microservice connects to RabbitMQ and PostgreSQL based on environment variables provided in the Docker Compose setup.

- **Database Interaction**:
  - The Data Service uses SQLAlchemy to interact with a PostgreSQL database.
  - A simple data model is defined with a `DataRecord` table, which includes columns such as `request_id`, `item_type`, `table_name`, and `payload`.
  - Current table mappings (e.g., `"table1"` for animals and `"table2"` for plants) are placeholders for future, more dynamic data routing logic.

- **Current Limitations and Future Enhancements**:
  - **Entitlement Service**: The inline RBAC logic and usage of `auth_utils` are temporary measures. Future work will integrate a full-fledged AuthZ server and remove deprecated code.
  - **Data Service**: Error handling, response mechanisms for non-GET operations, and more sophisticated table mapping are planned improvements.
  - **Service Initialization**: The current use of fixed startup delays (e.g., 10-second sleeps) is a temporary workaround to handle dependency readiness issues. Future updates will implement robust health checks.
  - **Error and Response Handling**: There is minimal error feedback or retry logic at this stage. Enhancements will be added to ensure better resilience and client communication.

This README provides a concise yet comprehensive overview of EHmicroService, offering the necessary context for future developers or AI systems to understand the project's design, current functionality, and planned evolution.
# EHmicroService

EHmicroService is a microservices-based framework that demonstrates an event-driven architecture using RabbitMQ for messaging and PostgreSQL for data persistence. This project is an evolving starting point for a generic framework and is intended for future expansion and refinement.

## Architecture Overview

- **Microservices Components**:
  - **Controller Service**: Receives incoming API requests from the `frontdoor` RabbitMQ queue and routes them for further processing. It forwards requests to the entitlement check queue and, upon receiving a pass response, directs data-related requests to the Data Service.
  - **Entitlement Service**: Validates requests based on Role-Based Access Control (RBAC). Currently, it uses inline logic and a JSON-based rule set (from `entitlement_rules.json`) to determine access. In future iterations, this service will delegate to a dedicated AuthZ server for more robust authorization.
  - **Data Service**: Handles CRUD operations by interacting with a PostgreSQL database. It uses placeholder logic to map requests (e.g., categorizing "animals" to `table1` and "plants" to `table2`) and processes operations based on the HTTP method specified (GET, POST, PUT, DELETE). Future enhancements will introduce more sophisticated data mapping and error/response handling.

- **Messaging Flow**:
  1. A client publishes a message (including fields like `request_id`, `token`, `method`, and `item_type`) to the `frontdoor` queue.
  2. The **Controller Service** consumes the message and forwards it to the appropriate entitlement check queue.
  3. The **Entitlement Service**:
     - Decodes the provided token (using a now-deprecated `auth_utils` module) to determine the user role.
     - Applies inline RBAC checks (currently using hardcoded logic with reference to `entitlement_rules.json` for context) to decide if the request should pass.
     - For approved requests, it publishes the message to a designated “pass” queue (either for the Controller or Data Service). Rejected messages are sent to a `REJECTED` queue.
  4. For data-related requests, the **Data Service**:
     - Listens on its request queue, performs basic table mapping based on the `item_type`, and then proceeds with the database operation.
     - For GET requests, it queries the database and publishes the results to the `frontdoor_output` queue.
     - For POST, PUT, and DELETE operations, it currently executes the database operation without sending a detailed response back to the client.

- **Message Identification and Flow Tracking**:
  - Each message carries a `request_id` to enable tracing through the system’s logs. This ID is manually generated for now and serves as a placeholder for more advanced correlation mechanisms in the future.
  - The project uses RabbitMQ queues such as `frontdoor`, entitlement check queues (`CONTROLLER_ENTITLEMENT_CHECK` and `DATA_ENTITLEMENT_CHECK`), pass queues (`CONTROLLER_ENTITLEMENT_PASS` and `DATA_ENTITLEMENT_PASS`), and a response queue (`FRONTDOOR_OUTPUT`).

## Implementation Details

- **Configuration**:
  - A shared configuration module (`config.py`) defines environment variables and queue names, ensuring consistency across services.
  - Each microservice connects to RabbitMQ and PostgreSQL based on environment variables provided in the Docker Compose setup.

- **Database Interaction**:
  - The Data Service uses SQLAlchemy to interact with a PostgreSQL database.
  - A simple data model is defined with a `DataRecord` table, which includes columns such as `request_id`, `item_type`, `table_name`, and `payload`.
  - Current table mappings (e.g., `"table1"` for animals and `"table2"` for plants) are placeholders for future, more dynamic data routing logic.

- **Current Limitations and Future Enhancements**:
  - **Entitlement Service**: The inline RBAC logic and usage of `auth_utils` are temporary measures. Future work will integrate a full-fledged AuthZ server and remove deprecated code.
  - **Data Service**: Error handling, response mechanisms for non-GET operations, and more sophisticated table mapping are planned improvements.
  - **Service Initialization**: The current use of fixed startup delays (e.g., 10-second sleeps) is a temporary workaround to handle dependency readiness issues. Future updates will implement robust health checks.
  - **Error and Response Handling**: There is minimal error feedback or retry logic at this stage. Enhancements will be added to ensure better resilience and client communication.


## Data Flow Diagram

```mermaid
sequenceDiagram
    participant Client
    participant RabbitMQ
    participant ControllerService
    participant EntitlementService
    participant DataService
    participant PostgreSQL

    %% Initial request flow from the client to the controller
    Client->>RabbitMQ: Publish request to 'frontdoor'
    RabbitMQ->>ControllerService: Deliver message from 'frontdoor'
    ControllerService->>RabbitMQ: Publish to 'CONTROLLER_ENTITLEMENT_CHECK'
    
    %% First entitlement check for controller-level authorization
    RabbitMQ->>EntitlementService: Deliver message from 'CONTROLLER_ENTITLEMENT_CHECK'
    alt RBAC Pass (Controller Check)
        EntitlementService->>RabbitMQ: Publish to 'CONTROLLER_ENTITLEMENT_PASS'
    else RBAC Fail
        EntitlementService->>RabbitMQ: Publish to 'REJECTED'
    end
    RabbitMQ->>ControllerService: Deliver message from 'CONTROLLER_ENTITLEMENT_PASS'
    
    %% Forwarding data requests to the Data Service
    ControllerService->>RabbitMQ: Publish to 'DATA_REQUEST' (if request_type is data)
    RabbitMQ->>DataService: Deliver message from 'DATA_REQUEST'
    
    %% Data Service maps the request and triggers a second entitlement check
    DataService->>DataService: Map item_type to table (e.g., animals → table1, plants → table2)
    DataService->>RabbitMQ: Publish to 'DATA_ENTITLEMENT_CHECK'
    RabbitMQ->>EntitlementService: Deliver message from 'DATA_ENTITLEMENT_CHECK'
    alt RBAC Pass (Data Check)
        EntitlementService->>RabbitMQ: Publish to 'DATA_ENTITLEMENT_PASS'
    else RBAC Fail
        EntitlementService->>RabbitMQ: Publish to 'REJECTED'
    end
    RabbitMQ->>DataService: Deliver message from 'DATA_ENTITLEMENT_PASS'
    
    %% Data Service performs the database operation based on method type
    DataService->>PostgreSQL: Execute DB operation (GET, POST, PUT, DELETE)
    alt GET Operation
        PostgreSQL-->>DataService: Return query results
        DataService->>RabbitMQ: Publish response to 'FRONTDOOR_OUTPUT'
        RabbitMQ->>Client: Deliver response
    else Non-GET Operation
        PostgreSQL-->>DataService: Confirm DB operation
        Note right of DataService: Logging only (no client response)
    end



##Project Structure

The updated project structure is as follows:

EHmicroService/
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

