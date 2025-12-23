import os
import requests
from typing import List
from rigour.env import env_opt, env_str


def get_env_list(name: str, default: List[str] = []) -> List[str]:
    value = env_opt(name)
    if value is not None:
        values = value.split(":")
        if len(values):
            return values
    return default


MODEL_PATH = os.path.join(os.path.dirname(__file__), "schema")
MODEL_PATH = env_str("FTM_MODEL_PATH", MODEL_PATH)

USER_AGENT = env_str("FTM_USER_AGENT", requests.utils.default_user_agent())
