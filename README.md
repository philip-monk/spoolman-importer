# Spoolman Importer 🎉

Python script to manage your filaments in a [SpoolmanDB](https://github.com/Donkie/SpoolmanDB) format, facilitating the creation and maintenance of a comprehensive and centralized filament database. This database is used in [Spoolman](https://github.com/Donkie/Spoolman) by [Donkie](https://github.com/Donkie).

## Installation

### Using Docker

You can use the pre-built Docker image from GitHub Container Registry.

1. Pull the Docker image:

```bash
docker pull ghcr.io/fwartner/spoolman-importer:main
```

2. Create an `.env` file based on `.env.example` and add your Spoolman URL:

```
SPOOLMAN_URL=http://your-spoolman-url:port
```

3. Run the Docker container with the desired action (create or delete):

To create vendors and filaments:
```bash
docker run --env-file .env ghcr.io/fwartner/spoolman-importer:main create
```

To delete all vendors and filaments:
```bash
docker run --env-file .env ghcr.io/fwartner/spoolman-importer:main delete
```

### Local Setup

1. Clone the repository and install dependencies:

```bash
git clone https://github.com/fwartner/spoolman-importer.git
cd spoolman-importer
pip install -r requirements.txt
```

2. Create an `.env` file based on `.env.example` and add your Spoolman URL:

```
SPOOLMAN_URL=http://your-spoolman-url:port
```

## Usage/Examples

### Create Data

To create vendors and filaments from the provided JSON data, run:

```bash
python main.py create
```

### Delete Data

To delete all vendors and filaments from your Spoolman instance, run:

```bash
python main.py delete
```

## Summary

The script will provide a summary of actions taken during the execution, such as the number of vendors and filaments created or merged.
