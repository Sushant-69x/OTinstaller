"""Responsible use notice text."""

NOTICE_TEXT = """RESPONSIBLE USE NOTICE
otinstaller installs and runs third-party open-source tools. It does not create,
own, endorse or verify them. Many are dual-use: used for fraud investigations,
journalism, security research and compliance, but capable of misuse.

You are solely responsible for how you use these tools and for complying with all
applicable laws, including privacy, data-protection and computer-misuse laws in your
jurisdiction, and the terms of any service you query. Use them only on targets you
are authorized to investigate. Do not use them to harass, stalk or harm anyone.

Tools are provided as-is, without warranty. Their authors and the otinstaller
contributors accept no liability for misuse."""

NOTICE_SHORT = (
    "You are solely responsible for how you use these tools and for complying with all "
    "applicable laws. Use them only on targets you are authorized to investigate."
)

NOTICE_VERSION = "1"


def has_accepted() -> bool:
    """Check if the user has accepted the notice."""
    import json

    from otinstaller.config import get_accept_path

    path = get_accept_path()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
        return data.get("version") == NOTICE_VERSION
    except (json.JSONDecodeError, OSError):
        return False


def record_acceptance() -> None:
    """Record the user's acceptance of the notice."""
    import datetime
    import json
    import os

    from otinstaller.config import get_accept_path

    path = get_accept_path()
    data = {
        "version": NOTICE_VERSION,
        "accepted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data))
    os.chmod(path, 0o600)
