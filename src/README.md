# Celery Worker App

This is a Celery worker application for asynchronous task processing.

## Getting Started

### Prerequisites

- Python 3.12+
- Redis server running (used as message broker)
- Requirements installed from requirements.txt

### Configuration

The worker uses Redis as both the message broker and result backend. Configure the connection settings in `.env`:

### Running the Worker

Start the Celery worker with:
```bash
PYTHONPATH=$PYTHONPATH:. celery -A worker.eval_app worker --loglevel=INFO -P solo
```
