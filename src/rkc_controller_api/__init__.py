# This file makes 'rkc_controller_api' a Python package.
import logging

# Configure basic logging for the package if not already configured by main app
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

