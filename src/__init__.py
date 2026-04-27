import os
import sys
from pathlib import Path
from .initializer import check_node
from .logger import logger

current_file_path = Path(__file__).resolve()
current_dir = current_file_path.parent
JS_SCRIPT_PATH = current_dir / 'javascript'

try:
    execute_dir = os.path.split(os.path.realpath(sys.argv[0]))[0]
except Exception:
    execute_dir = str(Path.cwd())

node_execute_dir = Path(execute_dir) / 'node'
current_env_path = os.environ.get('PATH', '')

try:
    if node_execute_dir.exists():
        os.environ['PATH'] = str(node_execute_dir) + os.pathsep + current_env_path
except Exception as e:
    logger.warning(f"Failed to update PATH environment: {e}")

try:
    check_node()
except Exception as e:
    logger.error(f"Node.js check failed: {e}")
