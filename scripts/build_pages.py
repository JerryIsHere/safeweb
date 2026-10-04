import argparse
import os
from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_site(output_dir: Path, asset_version: str = "dev") -> None:
    template_dir = PROJECT_ROOT / "web" / "templates"
    static_dir = PROJECT_ROOT / "web" / "static"
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
    )
    template = environment.get_template("index.html")
    html = template.render(
        home_url="./",
        asset_version=asset_version,
        url_for=lambda endpoint, filename: f"static/{filename}",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(static_dir, output_dir / "static", dirs_exist_ok=True)
    (output_dir / ".nojekyll").touch()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "_site")
    parser.add_argument("--asset-version", default=os.getenv("GITHUB_SHA", "dev"))
    arguments = parser.parse_args()
    build_site(arguments.output_dir, arguments.asset_version)


if __name__ == "__main__":
    main()