def str_env_to_bool(env: str|None) -> bool:
    if env is None:
        return False
    return env.lower() in ("yes", "true", "t", "1")