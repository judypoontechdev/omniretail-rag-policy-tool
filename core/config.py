import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve project base directory and locate .env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

# Load environment variables from .env file
load_dotenv(dotenv_path=ENV_PATH)

# Paths configuration
DATA_DIR = BASE_DIR / "data"
POLICY_MD_PATH = str(DATA_DIR / "policy.md")
CSV_PATH = str(DATA_DIR / "customer_data.csv")
EVAL_CSV_PATH = str(DATA_DIR / "eval_testset.csv")
CHROMA_PERSIST_DIR = str(BASE_DIR / "chroma_db")

# API Keys configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")