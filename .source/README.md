# Source bundle

The complete project source and all documentation are stored as 14 numbered base64 text shards in `parts/`. The repository's extraction helpers reconstruct the archive and verify its SHA-256 checksum before extraction.

Run from the repository root:

- Linux/macOS: `bash extract-source.sh`
- Windows PowerShell: `.\extract-source.ps1`

The resulting project folder is `agentic-ml-department/`. Run Docker Compose from that folder.
