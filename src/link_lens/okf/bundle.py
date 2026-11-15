"""Write a release's OKF tree to a folder, through the same renderer the tree uses."""

from pathlib import Path

from sqlalchemy import text

from .. import store
from . import render, tree


def put(root, files):
    """Write `path: text` under a folder."""
    root = Path(root)
    for path, body in files.items():
        target = root / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)


def paths(connection, release, sources=None):
    """Every page and index path of a release that `sources` may see."""
    scope, parameters = tree.visible(sources)
    parameters["release"] = release["release_id"]
    pages = list(
        connection.execute(
            text(
                "SELECT path FROM serving.okf_page "
                f"WHERE release_id = :release {scope} ORDER BY path"
            ),
            parameters,
        ).scalars()
    )
    folders = connection.execute(
        text(
            "SELECT DISTINCT parent FROM serving.okf_index "
            f"WHERE release_id = :release {scope}"
        ),
        parameters,
    ).scalars()
    return pages + [render.index_path(parent) for parent in folders]


def write_tree(connection, release, root, sources=None):
    """Write every page and index of a release under `root`. Returns the paths.

    Each file holds exactly what `tree.read` returns for its path.
    """
    written, cache = paths(connection, release, sources), {}
    for path in written:
        put(root, {path: tree.page_text(connection, release, path, sources, cache)})
    return written


def write(release_id, root, sources=None):
    """Write a release under `root` on a connection of its own. Returns counts."""
    with store.engine().connect() as connection:
        release = tree.release_record(connection, release_id)
        written = write_tree(connection, release, root, sources)
    return {**release, "files": len(written), "root": str(root)}
