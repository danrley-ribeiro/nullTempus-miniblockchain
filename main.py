import os
import sys

def init_env():
    os.makedirs("data", exist_ok=True)

if __name__ == "__main__":
    init_env()
    from cli.menu import main_cli
    
    try:
        main_cli()
    except KeyboardInterrupt:
        print("\nSaindo...")
        sys.exit(0)
