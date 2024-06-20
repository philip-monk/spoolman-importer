# Spoolman Importer 🎉

Python script to manage your filaments in a [SpoolmanDB](https://github.com/Donkie/SpoolmanDB) format, facilitating the creation and maintenance of a comprehensive and centralized filament database. This database is used in [Spoolman](https://github.com/Donkie/Spoolman) by [Donkie](https://github.com/Donkie).

## Installation

Clone the repository and install the dependencies:

```bash
git clone <repo_url>
cd <repo_directory>
pip install -r requirements.txt
```

## Environment Variables

Create an `.env` file based on `.env.example` and add your Spoolman URL:

```
SPOOLMAN_URL=http://your-spoolman-url:port
```

## Usage/Examples

You can use the script to either create or delete data in your Spoolman instance.

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

The script will provide a summary of actions taken during the execution, such as the number of vendors and filaments created or merged. Skipped items will not be included in the summary.
