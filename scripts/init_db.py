from app.config import get_settings
from app.database import init_db


def main() -> None:
    settings = get_settings()
    init_db(settings)
    print("Database initialized.")


if __name__ == "__main__":
    main()
