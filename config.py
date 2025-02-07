import os

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://myuser:mysecretpassword@localhost:5432/mydb")

# Other queue names remain defined here
FRONTDOOR = "frontdoor"
CONTROLLER_ENTITLEMENT_CHECK = "controller_entitlement_check"
CONTROLLER_ENTITLEMENT_PASS = "controller_entitlement_pass"
DATA_REQUEST = "data_request"
DATA_ENTITLEMENT_CHECK = "data_entitlement_check"
DATA_ENTITLEMENT_PASS = "data_entitlement_pass"
REJECTED = "rejected"

ALL_QUEUES = [
    FRONTDOOR,
    CONTROLLER_ENTITLEMENT_CHECK,
    CONTROLLER_ENTITLEMENT_PASS,
    DATA_REQUEST,
    DATA_ENTITLEMENT_CHECK,
    DATA_ENTITLEMENT_PASS,
    REJECTED
]

def declare_all_queues(channel):
    for q in ALL_QUEUES:
        channel.queue_declare(queue=q)
