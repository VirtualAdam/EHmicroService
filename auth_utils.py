# auth_utils.py

TOKEN_ROLE_MAP = {
    "token_app_1": "green",
    "token_app_2": "blue",
    "token_malicious": "red"
    # If no match => 'purple'
}

def decode_token(token: str) -> str:
    """
    Convert a token into an internal role: 'green', 'blue', 'red', or 'purple' (unknown).
    """
    clean_token = token.strip().lower()
    return TOKEN_ROLE_MAP.get(clean_token, "purple")

# Role-based table access rules:
# - green => can access table1 and table2
# - blue => can only access table2
# - red/purple => can't access any table
def can_access_table(role: str, table: str) -> bool:
    if role == "green":
        return table in ["table1", "table2"]
    elif role == "blue":
        return table == "table2"
    else:
        # red or purple => no access
        return False
