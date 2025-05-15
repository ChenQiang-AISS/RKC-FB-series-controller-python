import logging
from typing import Optional

# Assuming fb_controller is in src/ and Python path is set up correctly
# If src is not in PYTHONPATH, adjust import or project structure
from fb_controller.rkc_communication import RKCCommunication
from rkc_controller_api.config import settings

logger = logging.getLogger(__name__)

class RKCManager:
	"""
	Manages the RKCCommunication instance and interactions with the controller.
	"""
	def __init__(self):
		self.comm: Optional[RKCCommunication] = None
		self.is_connected: bool = False
		self.current_temperature: Optional[float] = None
		self.target_temperature: Optional[float] = None
		self.output_value: Optional[float] = None

	def connect(self):
		"""Establishes connection to the RKC controller."""
		if self.is_connected and self.comm:
			logger.info("Already connected to RKC controller.")
			return True
		try:
			logger.info(
				"Attempting to connect to RKC controller on port %s at address %s with baudrate %s.",
				settings['serial_port'],
				settings['controller_address'],
				settings['baudrate']
			)
			# RKCCommunication uses a context manager, but for a long-lived object,
			# we manage open/close manually or adapt the class.
			# For now, let's assume we can instantiate and then call a connect-like method
			# or that __enter__ is implicitly handled if we were to use `with`.
			# The provided RKCCommunication opens serial on __enter__.
			# We will create it and it will be "active" until closed.
			self.comm = RKCCommunication(
				port=settings['serial_port'],
				address=settings['controller_address'],
				baudrate=settings['baudrate'],
				timeout=settings['timeout']
			)
			self.comm.open()
			# The RKCCommunication class provided doesn't have a separate connect method.
			# It opens the port in __enter__. For a long-lived server,
			# we might need to adapt it or manage the serial.Serial object more directly.
			# For this prototype, we'll assume instantiating it is enough and
			# methods will work. A better approach would be an explicit open/close.
			# Let's simulate an open by trying a read.
			# To truly "open" it without context manager, we'd do:
			# self.comm.ser = serial.Serial(...)
			# For now, we rely on methods to handle serial operations.
			# A test read can confirm connectivity.
			pv_test = self.comm.read_value() # Assuming read_pv exists as suggested
			if pv_test is not None:
				logger.info("Successfully connected to RKC controller. Initial PV: %s", pv_test)
				self.is_connected = True
				self.current_temperature = pv_test
			else:
				# If RKCCommunication opens port on first operation, this might be complex.
				# The original RKCCommunication opens port in __enter__.
				# For a persistent server, you might want to modify RKCCommunication
				# to have explicit open() and close() methods that are not tied to __enter__/__exit__.
				# For this prototype, we'll assume it can be used after instantiation.
				# If it fails, it will log errors during operations.
				logger.warning("RKC Controller connection might have issues. Test read failed but proceeding.")
				# We'll set is_connected to True and let operations fail if port isn't truly open.
				# This part is tricky with the current RKCCommunication design for long-lived apps.
				# A robust solution would refactor RKCCommunication.
				self.is_connected = True # Optimistic, actual check happens on ops.

		except Exception as e:
			logger.error("Failed to connect to RKC controller: %s", e, exc_info=True)
			self.is_connected = False
			self.comm = None
		return self.is_connected

	def disconnect(self):
		"""Closes connection to the RKC controller."""
		if self.comm and hasattr(self.comm, 'close') and self.is_connected:
			try:
				self.comm.close()
				logger.info("Disconnected from RKC controller.")
			except Exception as e:
				logger.error("Error during RKC controller disconnection: %s", e, exc_info=True)
		self.is_connected = False
		self.comm = None

	def get_status(self) -> tuple[Optional[float], Optional[float], Optional[float]]:
		"""Reads current_temperature, target_temperature, and output_value from the controller."""
		if not self.is_connected or not self.comm:
			logger.warning("Not connected to RKC controller. Cannot get status.")
			return None, None, None

		try:
			self.current_temperature = self.comm.read_value()
			self.target_temperature = float(self.comm.poll(identifier="S1"))  # Reading output value 
			self.output_value = float(self.comm.poll(identifier="O1"))  # Reading output value
			logger.debug("Read status: current_temperature=%s, target_temperature=%s, output_value=%s",
				self.current_temperature, self.target_temperature, self.output_value)
			return self.current_temperature, self.target_temperature, self.output_value
		except Exception as e:
			logger.error("Error reading status from RKC controller: %s", e, exc_info=True)
			# Potentially mark as disconnected if errors persist
			return self.current_temperature, self.target_temperature, self.output_value # Return last known values

	def set_temperature(self, temperature: float) -> bool:
		"""Sets the target temperature (SV) on the controller.

		Args:
			temperature (float): The temperature to set.

		Returns:
			bool: True if successful, False otherwise.
		"""
		if not self.is_connected or not self.comm:
			logger.warning("Not connected to RKC controller. Cannot set temperature.")
			return False
		try:
			self.comm.set_value(temperature)
			logger.info("Sent command to set temperature to %s", temperature)
			self.target_temperature = temperature
			return True
		except Exception as e:
			logger.error("Error setting temperature on RKC controller: %s", e, exc_info=True)
			return False

# Global instance of RKCManager
# This will be initialized and managed by the FastAPI app's lifespan events.
rkc_handler: Optional[RKCManager] = None

def get_rkc_manager() -> RKCManager:
	"""Dependency injector for RKCManager."""
	if rkc_handler is None:
		# This should ideally not happen if lifespan management is correct
		raise RuntimeError("RKCManager not initialized. Ensure FastAPI lifespan events are configured.")
	return rkc_handler
