"""Generate the report from the approved user-supplied text."""

from generate_user_report import SOURCE, make_document


if __name__ == "__main__":
    make_document(SOURCE.read_text(encoding="utf-8"))
