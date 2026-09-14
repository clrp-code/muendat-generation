# built-in modules
from os import getenv
from pathlib import Path

# third party libraries

# user-defined classes


class SystemInfo:

	def __init__(self):

		self._egs_home_path = getenv("EGS_HOME")
		if self._egs_home_path is None:
			print("You must set the EGS_HOME environment variable set")
			raise SystemExit()
		self.egs_home = Path(self._egs_home_path).resolve()

		self._brachy_lib_path = self._egs_home_path + "/egs_brachy/lib/"
		if not Path(self._brachy_lib_path).is_dir():
			self._brachy_lib = self._egs_home_path + "/egs_brachy/egs_brachy/lib/"
			if not Path(self._brachy_lib).is_dir():
				print("Couldn't find your egs_brachy lib directory")
				raise SystemExit()
		self.brachy_lib = Path(self._brachy_lib).resolve()

		self._hen_house_path = getenv("HEN_HOUSE")
		if self._hen_house_path is None:
			print("No HEN_HOUSE environment variable set, inferring from EGS_HOME")
			self._hen_house_path = self._egs_home_path + "/../HEN_HOUSE/"
			if not Path(self._hen_house_path).is_dir():
				print("Could not infer HEN_HOUSE location")
				raise SystemExit()
		self.hen_house = Path(self._hen_house_path).resolve()

		self.g = self.egs_home / "g"
		self.generation = self.egs_home / "g" / "muendat-generation"

sys_info = SystemInfo()
