"""Write a release's OKF tree to a folder, through the same renderer the tree uses."""

from pathlib import Path

from sqlalchemy import text

from .. import releases, store
from . import render, tree


def write(release_id, root, sources=None):
    """Write every page and index of a release under `root`. Returns counts.

    Each file holds exactly what `tree.read` returns for its path.
    """
    root = Path(root)
    scope, parameters = tree.visible(sources)
    with store.engine().connect() as connection:
        release = releases.get(connection, release_id)
        parameters["release"] = release["release_id"]
        paths = list(
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
        paths += [render.index_path(parent) for parent in folders]
        for path in paths:
            target = root / path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(tree.page_text(connection, release, path, sources))
    return {**release, "files": len(paths), "root": str(root)}
