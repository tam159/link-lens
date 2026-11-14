"""Where artifact bytes live. Content is addressed by SHA-256 in every backend.

`catalog.artifact.uri` records where each artifact's bytes are, so artifacts in
the local directory and in object storage can coexist while blobs move.
"""

import hashlib
from functools import lru_cache
from pathlib import Path

from .settings import settings


def relative(sha):
    return f"blobs/{sha[:2]}/{sha}"


class LocalBlobStore:
    """Bytes under the artifact directory. URIs are relative to it."""

    scheme = "local"

    def __init__(self, root: Path):
        self.root = root

    def uri(self, sha):
        return "local:" + relative(sha)

    def put(self, sha, data):
        path = self.root / relative(sha)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            temp = path.with_suffix(".tmp")
            temp.write_bytes(data)
            temp.replace(path)
        return self.uri(sha)

    def path(self, uri, sha):
        path = self.root / relative(sha)
        if not path.is_file():
            raise FileNotFoundError(sha)
        return path


class S3BlobStore:
    """Bytes in an S3-compatible bucket, read through a local cache.

    Callers need a file path, so an object is downloaded once into `cache`,
    verified against its hash, and served from there afterwards.
    """

    scheme = "s3"

    def __init__(self, bucket, prefix, cache: Path, client=None, endpoint_url=None):
        self.bucket, self.prefix, self.cache = bucket, prefix.strip("/"), cache
        self._client, self.endpoint_url = client, endpoint_url

    def client(self):
        if self._client is None:
            try:
                import boto3
            except ImportError as error:
                raise RuntimeError(
                    "The S3 artifact store needs boto3: uv sync --group s3"
                ) from error
            self._client = boto3.client("s3", endpoint_url=self.endpoint_url)
        return self._client

    def key(self, sha):
        return "/".join(part for part in (self.prefix, relative(sha)) if part)

    def uri(self, sha):
        return f"s3://{self.bucket}/{self.key(sha)}"

    def put(self, sha, data):
        self.client().put_object(Bucket=self.bucket, Key=self.key(sha), Body=data)
        return self.uri(sha)

    def fetch(self, uri):
        """The bytes at a URI, straight from the bucket."""
        bucket, _, key = uri.removeprefix("s3://").partition("/")
        return self.client().get_object(Bucket=bucket, Key=key)["Body"].read()

    def path(self, uri, sha):
        path = self.cache / relative(sha)
        if not path.is_file():
            data = self.fetch(uri)
            if hashlib.sha256(data).hexdigest() != sha:
                raise ValueError(f"Artifact {sha} does not match its hash in {uri}")
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_suffix(".tmp")
            temp.write_bytes(data)
            temp.replace(path)
        return path


@lru_cache
def stores():
    """The configured backends by URI scheme. New artifacts go to the first."""
    config = settings()
    local = LocalBlobStore(config.artifact_dir)
    if config.artifact_store == "s3":
        if not config.artifact_bucket:
            raise ValueError("LINK_LENS_ARTIFACT_BUCKET is required for the S3 store")
        remote = S3BlobStore(
            config.artifact_bucket,
            config.artifact_prefix,
            config.artifact_dir / "s3-cache",
            endpoint_url=config.artifact_endpoint_url,
        )
        return {"s3": remote, "local": local}
    return {"local": local}


def put(sha, data):
    """Write bytes to the configured backend and return their URI."""
    return next(iter(stores().values())).put(sha, data)


def path(uri, sha):
    """A local file holding the artifact's bytes, wherever its URI points."""
    scheme = "s3" if uri.startswith("s3://") else "local"
    if scheme not in stores():
        raise ValueError(f"No artifact store is configured for {uri}")
    return stores()[scheme].path(uri, sha)


def presigned(uri, seconds, filename):
    """A link to an artifact that expires, signed by its store; None if local."""
    if not uri.startswith("s3://") or "s3" not in stores():
        return None
    bucket, _, key = uri.removeprefix("s3://").partition("/")
    return (
        stores()["s3"]
        .client()
        .generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
                "ResponseContentType": "application/gzip",
            },
            ExpiresIn=seconds,
        )
    )
