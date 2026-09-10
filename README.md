# Flux RDM

Flux RDM is a high-performance, containerized remote desktop session and credential manager built with PyQt6. It provides a secure, organized workspace to manage RDM connections, vault credentials, and direct host access.

## Features

* **Hierarchical Session Management**: Organize RDM connections and custom folders in a clean, filterable tree view.
* **Credential Vault**: Securely manage shared vault credentials and apply them globally or scoped to specific folders.
* **Inline Dashboard Metrics**: Real-time telemetry monitoring configured nodes, active groups, vault coverage, and unprotected endpoints.
* **Vector SVG UI Elements**: Custom-rendered vector icons and UI components designed to run seamlessly in minimal Linux container environments without requiring system-level emoji font packages.
* **Direct Ad-hoc Connections**: Quick-connect toolbar for ad-hoc host targeting and instant session launching.
* **Import & Export Support**: Easily ingest Devolutions `.rdm` configurations and export datasets to CSV spreadsheets or `.rdp` session archive bundles.

## Project Structure

```text
├── app
│   ├── exporter.py
│   ├── main.py
│   ├── parser.py
│   ├── storage
│   │   └── database.py
│   ├── ui
│   │   ├── dashboard_view.py
│   │   ├── edit_dialog.py
│   │   ├── main_window.py
│   │   ├── rdp_viewer.py
│   │   └── theme.py
│   └── utils
│       └── picker.py
├── data
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── run.sh

```

## Requirements

* Python 3.10+
* PyQt6 & PyQt6-Svg
* Docker & Docker Compose (optional for containerized execution)

## Installation & Running (Docker)

1. Ensure Docker and Docker Compose are installed on your system.
2. Build and start the application container by running:
```bash
docker compose up --build

```

---

*Vibe coded by: Sanket Gawand*
