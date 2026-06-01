"""Convenience entrypoint for running SocratiCode with `python app.py`."""

from backend import config
from backend.main import app


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
