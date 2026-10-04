"""Export the Flask template and static assets as a GitHub Pages site."""

import argparse
import os
from pathlib import Path
import shutil

from jinja2 import Environment, FileSystemLoader, select_autoescape


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_site(output_dir: Path, api_base_url: str = "") -> None:
    template_dir = PROJECT_ROOT / "web" / "templates"
    static_dir = PROJECT_ROOT / "web" / "static"
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html"]),
    )
    template = environment.get_template("index.html")
    html = template.render(
        model_available=False,
        deployment_mode="static",
        api_base_url=api_base_url.rstrip("/"),
        home_url="./",
        url_for=lambda endpoint, filename: f"static/{filename}",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(static_dir, output_dir / "static", dirs_exist_ok=True)
    (output_dir / ".nojekyll").touch()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "_site")
    arguments = parser.parse_args()
    build_site(arguments.output_dir, os.getenv("SAFEWEB_API_URL", ""))


if __name__ == "__main__":
    main()