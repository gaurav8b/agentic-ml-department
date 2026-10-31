# Source snapshot and publication

The compressed archive is a reproducible backup of the complete application source.

The GitHub Actions workflow `.github/workflows/publish-readable-source.yml` reconstructs the archive from the temporary base64 shards, verifies it against `CHECKSUMS.txt`, expands the project into ordinary repository paths, runs Python compilation and tests, and commits the readable source tree to `main`.

The normal source tree is the primary browsing and development interface. The archive is retained only as a checksum-verified backup.

For a local manual extraction, use `extract-source.sh` on Linux/macOS or `extract-source.ps1` on Windows. See `docs/MAKE_THE_POC_LIVE.md` for the full demonstration runbook.
