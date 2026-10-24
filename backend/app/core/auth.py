from fastapi import Header

def get_current_user_id(x_user_id: str = Header(default="default_user")) -> str:
    clean_id = x_user_id.strip() if x_user_id and x_user_id.strip() else "default_user"
    return clean_id
