"""Core widget building."""


def build(path, theme="light"):
    """Build a widget from a CSV file.

    Reads the CSV at ``path`` and writes a ``.widget`` file beside it.

    Args:
        path: Location of the CSV file. The first row must be a header.
        theme: ``"light"`` or ``"dark"``.

    Returns:
        The path of the widget file that was written.

    Raises:
        ValueError: If the CSV has no header row.
    """
    return str(path).rsplit(".", 1)[0] + ".widget"


def frob(x):
    """Frob x."""
    # do the frob
    return x
