# config.py

RABBITMQ_HOST = "localhost"

# Queue Names
FRONTDOOR = "frontdoor"
CONTROLLER_ENTITLEMENT_CHECK = "controller_entitlement_check"
CONTROLLER_ENTITLEMENT_PASS = "controller_entitlement_pass"
DATA_REQUEST = "data_request"
DATA_ENTITLEMENT_CHECK = "data_entitlement_check"
DATA_ENTITLEMENT_PASS = "data_entitlement_pass"
REJECTED = "rejected"

# All queues in one list
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
    """
    Declare all the queues in ALL_QUEUES on the given channel.
    This is idempotent: if a queue already exists, it's fine.
    """
    for q in ALL_QUEUES:
        channel.queue_declare(queue=q)
