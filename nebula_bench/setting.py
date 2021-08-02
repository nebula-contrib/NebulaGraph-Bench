# -*- coding: utf-8 -*-
import pathlib
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

WORKSPACE_PATH = pathlib.Path(__file__).parent.parent

DATA_FOLDER = os.environ.get("DATA_FOLDER") or "target/data/test_data"
REPORT_FOLDER = os.environ.get("REPORT_FOLDER") or "nginx/data"
NEBULA_SPACE = os.environ.get("NEBULA_SPACE") or "stress_test_{}".format(
    datetime.now().strftime("%m%d")
)
NEBULA_USER = os.environ.get("NEBULA_USER") or "root"
NEBULA_PASSWORD = os.environ.get("NEBULA_PASSWORD") or "nebula"
NEBULA_ADDRESS = os.environ.get("NEBULA_ADDRESS") or "127.0.0.1:9669"

DINGDING_SECRET = os.environ.get("DINGDING_SECRET")
DINGDING_WEBHOOK = os.environ.get("DINGDING_WEBHOOK")

if os.environ.get("NEBULA_MAX_CONNECTION"):
    NEBULA_MAX_CONNECTION = int(os.environ.get("NEBULA_MAX_CONNECTION"))
else:
    NEBULA_MAX_CONNECTION = 400

SQLALCHEMY_URI = os.environ.get("SQLALCHEMY_URI") or "sqlite:///./nebula-bench.db"
INFLUXDB_URL = os.environ.get("INFLUXDB_URL", None)
