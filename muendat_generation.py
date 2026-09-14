# built-in modules
from subprocess import run as cmd_run
from subprocess import PIPE, CalledProcessError
from datetime import datetime as dt

# third party libraries
import numpy as np

# user-defined classes
from system_info import sys_info
from diff_visualization import overlay_old_and_new_data, plot_diffs


def create_egsinp_for_material_named(material_name: str, pegsless: bool) -> None:
	"""
	Creates an input file for mu_en data for `material_name` with the `g` application
	"""

	file_contents=f"""
############################################
#
# Input file for the g application
# Based on the example at nrc-cnrc.github.io/EGSnrc/doc/pirs3100/
#
#  - Energy grid from 1 keV up to 1.5 MeV with 2000 gridpoints
#  - Calculation type 1 (photon beam only)
#  - Desired precision 0.1%
#
###########################################

# Application specific inputs

media= {material_name}
INITIAL RANDOM NO. SEEDS= 97, 33
Number of HISTORIES= 1000000000  # 1e9
precision= 0.001                 # target precision is 0.1%
calculation type= 1
verbose = no

:Start Source Input:
    INCIDENT SPECTRUM=       mono-energy-log-range
    INCIDENT KINETIC ENERGY= 0.001, 1.5, 5
    Incident Charge=         0
:Stop Source Input:

:Start MC Transport Parameter:
    Global ECUT=                    0.512
    Global PCUT=                    0.001
    Global SMAX=                    1e10
    Spin effects=                   On
    Rayleigh scattering=            On
    Photon cross sections=          xcom
    Pair cross sections=            nrc
    Triplet production=             On
    Bound Compton Scattering=       norej
    Radiative Compton corrections=  On
    Atomic relaxations=             On
    Photoelectron angular sampling= On
    Brems angular sampling=         KM
    Brems cross sections=           nrc
    Pair angular sampling=          KM
    ESTEPE=                         0.25
    XIMAX=                          0.5
    Electron Impact Ionization=     ik
    Skin depth for BCA=             3
    Boundary crossing algorithm=    exact
    Electron-step algorithm=        default
:Stop MC Transport Parameter:

:Start Media Definition:
    ae = 0.512
    ue = 2.511
    ap = 0.001
    up = 2.00
"""
	if pegsless:
		file_contents += f"    material data file = {str(sys_info.brachy_lib)}/media/material.dat\n"
	file_contents += ":Stop Media Definition:\n"

	with open(sys_info.g / f"{material_name}.egsinp", 'w') as f:
		f.write(file_contents)

def recall_cached_muen_for_material_named(material_name: str) -> tuple[str, list[float], list[float]]:
	"""
	Load the cached data for a newly-generated dataset that's help in /tmpmuen files. Returns
	(pegs4source, energies, muens).
	"""
	pegs4source = ""
	energies = []
	muens = []
	with open(sys_info.g / f"{material_name}.tmpmuen", "r") as f:
		for iline, line in enumerate(f):
			if iline == 0:
				pegs4source = line.strip()
				continue
			components = line.split()
			energies.append(float(components[0]))
			muens.append(float(components[1]))
	return pegs4source, energies, muens

def calculate_muen_for_material_named(
		material_name: str,
		prev_pegs4: str | None = None
) -> tuple[str, list[float], list[float]]:
	"""
	Creates an input file for the material, runs the input file through the g application, extracts the numerical
	datapoints from the logfile, outputs the extarcted data to a condensed .tmpmuen file, and cleans up the directory.
	This functions returns a tuple of (pegs4source, energies, muens)
	"""

	# Run the g application
	try:
		# try in pegsless mode first
		create_egsinp_for_material_named(material_name, pegsless=True)
		with open(sys_info.g / f"{material_name}.log", "w") as logfile:
			cmd_run(
				args = ["g", "-i", f"{material_name}.egsinp"],
				stdout = logfile,
			    cwd = sys_info.g,
				stderr = PIPE,
			    check = True
			)
			pegs4source = "egs_brachy/lib/media/material.dat"
	except CalledProcessError:
		# Failed to find the material in material.dat, will have to to a run with pegs4 input
		print(f"Trying with pegs4 input: suggested to be at {prev_pegs4}")
		if prev_pegs4 is None:
			raise SystemExit
		if prev_pegs4[-8:] == ".muendat":
			prev_pegs4 = prev_pegs4[:-8].split('/')[-1]
		print(f"Looking in {prev_pegs4}")

		try:
			create_egsinp_for_material_named(material_name, pegsless=False)
			with open(sys_info.g / f"{material_name}.log", "w") as logfile:
				cmd_run(
					args = ["g", "-i", f"{material_name}.egsinp", "-p", f"{prev_pegs4}"],
					stdout = logfile,
					cwd = sys_info.g,
					stderr = PIPE,
					check = True
				)
				pegs4source = f"HEN_HOUSE/pegs4/data/{prev_pegs4}.pegs4dat"
		except CalledProcessError:
			print(f"No new data possible for {material_name}. This material will not appear in the new dataset")
			return "", [], []

	# Extract the new data from the log file
	energies: list[float] = []
	muens: list[float] = []
	with open(sys_info.g / f"{material_name}.log", 'r') as f:
		for line in f:
			if line[:35] == "===> Incident kinetic energy (MeV):":
				energies.append(float(line.split()[5]))
			if line[:40] == "<mu_en/rho> = <E*mu_tr/rho>*(1-<g>)/Eave":
				muens.append(float(line.split()[4]))

	# Output data to a .tmpmuen file
	with open(sys_info.g / f"{material_name}.tmpmuen", 'w') as f:
		f.write(f"{pegs4source}\n")
		for energy, muen in zip(energies, muens):
			f.write(f"{energy:.6f} {muen:11.6f}\n")

	# Cleanup artifacts from the run
	egsinp_file = sys_info.g / f"{material_name}.egsinp"
	log_file = sys_info.g / f"{material_name}.log"
	mederr_file = sys_info.g / f"{material_name}.mederr"
	errors_file = sys_info.g / f"{material_name}.errors"
	egsinp_file.unlink()
	log_file.unlink()
	mederr_file.unlink()
	errors_file.unlink()

	return pegs4source, energies, muens

def extract_previous_muendat() -> dict[str, dict[str, tuple[str, list[float], list[float]]]]:
	"""
	Creates a dict of {muendat_name : {material_name: (pegs4src, energies, muens)}}
	"""
	muen_dir = sys_info.brachy_lib / "muen"
	muendat_files = [f.resolve() for f in muen_dir.iterdir() if (f.is_file() and f.suffix == ".muendat")]

	ret_dict = {}
	for muendat_file in muendat_files:

		file_dict = {}
		pegs4source = ""
		energies = []
		muens = []
		with open(muendat_file, 'r') as f:

			for line in f:
				if len(line) == 0:
					continue
				if line[0] == "#":  # Ignore easily-detactable comments
					continue
				components = line.split()
				if len(components) < 1:
					continue
				if components[0] == "Muen":
					material_name = line.split()[6]  # Muen values for medium MEDIUM = WATER_0.998
					if len(energies) > 0:
						file_dict[material_name] = pegs4source, energies, muens
					energies = []
					muens = []
				if components[0] == "Medium":
					pegs4source = line.split()[6]  # Medium used is WATER_0.998 found in brachy_xcom_1500keV
				if components[1] == "MeV":
					energies.append(float(components[0]))
					muens.append(float(components[2]))

			if len(energies) > 0:
				file_dict[material_name] = pegs4source, energies, muens

		ret_dict[muendat_file.stem] = file_dict

	return ret_dict

def aggregate_tmpmuens_into_new_muendat(
	new_data: dict[str, dict[str, tuple[str, list[float], list[float]]]]
) -> None:
	"""
	Searches the `g` directory for every .tmpmuen file
	and puts all data from these files into a single.muendat file
	"""
	for muendat_filename, file_data in new_data.items():
		with open(sys_info.g / f"{muendat_filename}.muendat", 'w') as outfile:
			outfile.write(f"#\n# {dt.now().replace(microsecond=0)}\n"
						  f"# This file was generated automatically using muendat_generation.py\n"
						  f"# See github.com/clrp-code/muendat-generation for details\n"
						  f"# All muen uncertainties are less than 0.1%\n#\n")
			for material_name in file_data.keys():
				pegs4source, energies, muens = file_data[material_name]
				outfile.write(f"Muen values for medium MEDIUM = {material_name}\n"
				              f"Medium used is {material_name} found in {pegs4source}\n"
				              f"Number of energy intervals is {len(energies)}\n")
				for energy, muen in zip(energies, muens):
					outfile.write(f"{energy:.6f} MeV {muen:11.6f} cm^2/g\n")


def main_loop(additional_material_names: list[str] | None = None) -> None:
	"""
	Finds old .muendat files in egs_brachy/lib, tries to replicate their results, and outputs
	the new data to the `g` directory with the same .muendat names. Plotting is done to compare new and old results.
	Additional materials specified in the __main__ function below are placed in a `new_materials.muendat` file
	"""
	if additional_material_names is None:
		additional_material_names = []

	material_old_new_dict = {}

	prev_data = extract_previous_muendat()
	new_data = {}
	for prev_muendat_filename, file_data in prev_data.items():
		print(f"\nWorking on {prev_muendat_filename}")
		file_dict = {}

		for material_name, mat_data in file_data.items():
			print(f"Working on {material_name}")

			prev_pegs4, prev_energies, prev_muens = mat_data
			if (sys_info.g / f"{material_name}.tmpmuen").is_file():
				pegs4source, energies, muens = recall_cached_muen_for_material_named(material_name)
			else:
				pegs4source, energies, muens = calculate_muen_for_material_named(material_name, prev_pegs4)

			if len(energies) > 0:
				file_dict[material_name] = pegs4source, energies, muens

			if len(prev_energies) != len(energies):
				print(f"Can't compare to previous .muendat: requested different number of new energies")
				continue

			material_old_new_dict[material_name] = energies, prev_muens, muens
			diffs = np.array(muens) - np.array(prev_muens)
			mean = diffs.mean()
			std = diffs.std()
			print(f"For material {material_name}, avg diff is {mean:.4f} with std {std:.4f} (rel_std = {mean/std:.4f})")

		new_data[prev_muendat_filename] = file_dict

	if "WATER_0.998" in material_old_new_dict:
		overlay_old_and_new_data(material_old_new_dict, "WATER_0.998")

	if len(material_old_new_dict) > 0:
		plot_diffs(material_old_new_dict)

	file_dict = {}
	for material_name in additional_material_names:
		print(f"Working on additional {material_name}")

		if (sys_info.g / f"{material_name}.tmpmuen").is_file():
			pegs4source, energies, muens = recall_cached_muen_for_material_named(material_name)
		else:
			pegs4source, energies, muens = calculate_muen_for_material_named(material_name)
		file_dict[material_name] = "egs_brachy/lib/media/material.dat", energies, muens

	new_data['new_materials'] = file_dict
	aggregate_tmpmuens_into_new_muendat(new_data)

if __name__ == "__main__":
	main_loop()
