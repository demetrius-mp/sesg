import os
import subprocess

from dotenv import load_dotenv


load_dotenv()

PYPI_TOKEN = os.getenv("PYPI_TOKEN")

if not PYPI_TOKEN:
    raise RuntimeError("Must set PYPI_TOKEN environment variable.")


def main():
    subprocess.run(
        "poetry build",
        shell=True,
    )

    subprocess.run(
        f'poetry publish -u "__token__" -p "{PYPI_TOKEN}"',
        shell=True,
    )


if __name__ == "__main__":
    main()
