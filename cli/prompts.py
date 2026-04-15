import getpass

def prompt_string(prompt: str) -> str:
    return input(f"{prompt}: ").strip()

def prompt_password(prompt: str) -> str:
    return getpass.getpass(f"{prompt}: ").strip()
