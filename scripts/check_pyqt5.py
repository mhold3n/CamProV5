import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import PyQt5  # noqa: F401
    logger.info("PyQt5 is installed")
except ImportError:
    logger.info("PyQt5 is not installed")