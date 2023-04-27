from pathlib import Path


def main():
    dist_folder = Path.cwd() / "dist"

    for file in dist_folder.iterdir():
        if file.is_file():
            file.unlink()


if __name__ == "__main__":
    main()
