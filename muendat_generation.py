# built-in modules
from subprocess import run as cmd_run
from subprocess import PIPE, CalledProcessError
from datetime import datetime as dt

# third party libraries
import numpy as np

# user-defined classes
from system_info import sys_info
from diff_visualization import overlay_old_and_new_data, plot_diffs

OUTPUT_LATEX_TABLES = False
SHOW_NEW_OLD_MUENS = False

def create_egsinp_for_material_named(material_name: str) -> None:
	"""
	Creates an input file for mu_en data for `material_name` with the `g` application
	"""

	file_contents=f"""
###############################################################################
#
# Input file for the g application
# Based on the example at nrc-cnrc.github.io/EGSnrc/doc/pirs3100/
#
#  - Energy grid from 1 keV up to 1.5 MeV with 2000 gridpoints
#  - Calculation type 1 (photon beam only)
#  - Desired precision 0.1%
#
###############################################################################


# Application specific inputs

media= {material_name}
INITIAL RANDOM NO. SEEDS= 97, 33
Number of HISTORIES= 1000000000  # 1e9
precision= 0.001                 # target precision is 0.1%
calculation type= 1
verbose = no

:Start Source Input:
    INCIDENT SPECTRUM=       mono-energy-log-range
    INCIDENT KINETIC ENERGY= 0.001, 1.5, 2000
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
    ae= 0.512
    ue= 2.511
    ap= 0.001
    up= 2.00
    material data file= {str(sys_info.brachy_lib)}/media/material.dat
:Stop Media Definition:
"""

	with open(sys_info.g / f"{material_name}.egsinp", 'w') as f:
		f.write(file_contents)

def recall_cached_muen_for_material_named(material_name: str) -> tuple[list[float], list[float]]:
	"""
	Load the cached data for a newly-generated dataset that's help in /tmpmuen files. Returns
	(energies, muens).
	"""
	energies = []
	muens = []
	with open(sys_info.g / f"{material_name}.tmpmuen", "r") as f:
		for iline, line in enumerate(f):
			components = line.split()
			energies.append(float(components[0]))
			muens.append(float(components[1]))
	return energies, muens

def calculate_muen_for_material_named(material_name: str) -> tuple[list[float], list[float]]:
	"""
	Creates an input file for the material, runs the input file through the g application, extracts the numerical
	datapoints from the logfile, outputs the extracted data to a condensed .tmpmuen file, and cleans up the directory.
	This functions returns a tuple of (energies, muens)
	"""

	# Run the g application
	try:
		create_egsinp_for_material_named(material_name)
		with open(sys_info.g / f"{material_name}.log", "w") as logfile:
			cmd_run(
				args = ["g", "-i", f"{material_name}.egsinp"],
				stdout = logfile,
			    cwd = sys_info.g,
				stderr = PIPE,
			    check = True
			)
	except CalledProcessError:
		# Failed to find the material in material.dat, will have to to a run with pegs4 input
		print(f"No run for {material_name}. This material will not appear in the new dataset")
		return [], []

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
		for energy, muen in zip(energies, muens):
			f.write(f"{energy:.6f} {muen:11.6f}\n")

	# Cleanup artifacts from the run
	egsinp_file = sys_info.g / f"{material_name}.egsinp"
	mederr_file = sys_info.g / f"{material_name}.mederr"
	errors_file = sys_info.g / f"{material_name}.errors"
	log_file = sys_info.g / f"{material_name}.log"
	egsinp_file.unlink(missing_ok=True)
	mederr_file.unlink(missing_ok=True)
	errors_file.unlink(missing_ok=True)
	log_file.unlink(missing_ok=True)

	return energies, muens

def extract_previous_muendat() -> dict[str, dict[str, tuple[list[float], list[float]]]]:
	"""
	Creates a dict of {muendat_name : {material_name: (energies, muens)}}
	"""
	muen_dir = sys_info.brachy_lib / "muen"
	muendat_files = [f.resolve() for f in muen_dir.iterdir() if (f.is_file() and f.suffix == ".muendat")]

	ret_dict = {}
	for muendat_file in muendat_files:
		print(f"\nExtracting from {muendat_file.stem}")

		file_dict = {}
		material_name = ""
		energies = []
		muens = []
		with open(muendat_file, 'r') as f:

			for line in f:
				line = line.strip()
				if len(line) == 0:
					continue
				if line[0] == "#":  # Ignore easily-detectable comments
					continue
				components = line.split()
				if len(components) < 1:
					continue
				if components[0] == "Muen":
					if len(energies) > 0:
						file_dict[material_name] = energies, muens
					material_name = line.split()[6]  # Muen values for medium MEDIUM = WATER_0.998
					energies = []
					muens = []
				if components[1] == "MeV":
					energies.append(float(components[0]))
					muens.append(float(components[2]))

			if len(energies) > 0:
				file_dict[material_name] = energies, muens

		ret_dict[muendat_file.stem] = file_dict

	return ret_dict

def aggregate_tmpmuens_into_new_muendat(new_data: dict[str, dict[str, tuple[list[float], list[float]]]]) -> None:
	"""
	Searches the `g` directory for every .tmpmuen file
	and puts all data from these files into a single.muendat file
	"""
	material_names = []
	with open(sys_info.g / f"materials_1500keV.muendat", 'w') as outfile:
		outfile.write(f"#\n# {dt.now().replace(microsecond=0)}\n"
					  f"# This file was generated automatically using muendat_generation.py\n"
					  f"# See github.com/clrp-code/muendat-generation for details\n"
					  f"# All muen uncertainties are less than 0.1%\n#\n")

		for muendat_filename, file_data in new_data.items():
			for material_name in file_data.keys():
				energies, muens = file_data[material_name]
				outfile.write(f"Muen values for medium MEDIUM = {material_name}\n"
							  f"Medium used is {material_name} found in egs_brachy/lib/media/material.dat\n"
							  f"Number of energy intervals is {len(energies)}\n"
							  f"Energy[MeV] Muen[cm^2/g]\n")
				for energy, muen in zip(energies, muens):
					outfile.write(f"{energy:.6f} {muen:11.6f}\n")
				material_names.append(material_name)

	if OUTPUT_LATEX_TABLES:
		format_as_latex(material_names)

def main_loop(additional_material_names: list[str] | None = None) -> None:
	"""
	Finds old .muendat files in egs_brachy/lib/muen, tries to replicate their results, and outputs
	the new data to the `g` directory with the same .muendat names. Plotting is done to compare new and old results.
	Additional materials specified in the __main__ function below are placed in a `new_materials.muendat` file
	"""
	if additional_material_names is None:
		additional_material_names = []

	material_old_new_dict = {}

	prev_data = extract_previous_muendat()
	new_data = {}
	ignored_list = []
	for prev_muendat_filename, file_data in prev_data.items():
		print(f"\nWorking on materials found in egs_brachy/lib/muen/{prev_muendat_filename}.muendat")
		file_dict = {}

		for material_name, mat_data in file_data.items():
			print(f"Working on {material_name}... ", end='', flush=True)

			prev_energies, prev_muens = mat_data
			energies, muens = [], []
			successful_cache_recall = False
			if (sys_info.g / f"{material_name}.tmpmuen").is_file():
				energies, muens = recall_cached_muen_for_material_named(material_name)
				if len(energies) > 0:
					successful_cache_recall = True
					print(f"extracted from cache")
				else:
					(sys_info.g / f"{material_name}.tmpmuen").unlink()

			if not successful_cache_recall:
				energies, muens = calculate_muen_for_material_named(material_name)
				if len(energies) > 0:
					print(f"done calculation")

			if len(energies) > 0:
				file_dict[material_name] = energies, muens
			else:
				ignored_list.append(material_name)
				continue

			if len(prev_energies) != len(energies):
				print(f"Can't compare to previous .muendat: requested different number of new energies")
				continue

			material_old_new_dict[material_name] = energies, prev_muens, muens
			rel_diffs = np.array(muens) /  np.array(prev_muens) - 1
			mean = rel_diffs.mean()
			std = rel_diffs.std()
			print(f"For material {material_name}, avg relative diff is {mean*100:.2f}% with std {std*100:.2f}%")
			if SHOW_NEW_OLD_MUENS:
				overlay_old_and_new_data(material_old_new_dict, material_name)

		new_data[prev_muendat_filename] = file_dict

	if len(material_old_new_dict) > 0:
		plot_diffs(material_old_new_dict)

	file_dict = {}
	for material_name in additional_material_names:
		print(f"Working on additional {material_name}")

		if (sys_info.g / f"{material_name}.tmpmuen").is_file():
			energies, muens = recall_cached_muen_for_material_named(material_name)
		else:
			energies, muens = calculate_muen_for_material_named(material_name)
		file_dict[material_name] = "egs_brachy/lib/media/material.dat", energies, muens

	new_data['new_materials'] = file_dict
	aggregate_tmpmuens_into_new_muendat(new_data)

	if len(ignored_list) > 0:
		print(f"We ignored \n{sorted(set(ignored_list))}")
	else:
		print(f"All materials were successfully generated ✓")

def format_as_latex(some_list: list[str]) -> None:

	some_list = sorted(list(set(some_list)))

	trimmed_list = []
	mixture_list_AC = [f"A{n}C{100-n}" for n in range(0, 105, 5)]
	mixture_list_PC = [f"P{n}C{100-n}" for n in range(0, 105, 5)]

	for entry in some_list:
		if entry in mixture_list_AC:
			continue
		if entry in mixture_list_PC:
			continue
		if entry in [
			"10GLAND-90ADIPOSE",
			"25GLAND-75ADIPOSE",
			"25GLAND-75ADIPOSE",
			"75GLAND-25ADIPOSE",
			"80ADIPOSE-20GLAND",
			"80ADIPOSE-20GLAND_M",
			"90GLAND-10ADIPOSE",
			"CALCIFICATION_AUS1_HCO",
			"CALCIFICATION_AUS1_O",
			"CALCIFICATION_AUS2_HCO",
			"CALCIFICATION_AUS2_O",
			"CALCIFICATION_AUS2_O",
			"CALCIFICATION_AUS3_HCO",
			"CALCIFICATION_AUS3_O",
			"CALCIFICATION_AUS4_HCO",
			"CALCIFICATION_AUS4_O",
			"PROSTATE_01PCALC",
			"PROSTATE_05PCALC",
			"PROSTATE_1PCALC",
			"PROSTATE_1p5PCALC",
			"PROSTATE_3PCALC",
			"PROSTATE_4PCALC",
			"PROSTATE_5PCALC"]:
			# don't include ALL the mixtures
			continue
		if "SS_" in entry or "%" in entry or "__" in entry:
			# small trim
			continue
		if "COLLSTRUCMECH" in entry or "BLOODFILLED" in entry:
			# too long for latex columns
			continue
		if len(entry) < 3:
			# don't include elements
			continue
		trimmed_list.append(entry)

	length = len(trimmed_list)
	one_third = len(trimmed_list) // 3
	for idx in range(one_third+1):
		out_str = ""
		for col in range(3):
			jdx = col * one_third + idx
			if jdx < length:
				name = r"\_".join(trimmed_list[jdx].split('_'))
				name = r"\%".join(name.split('%'))
				out_str += f" {name} &"

		print(f"{out_str[:-1]} \\\\")

if __name__ == "__main__":

	material_dat_media = []
	with open(sys_info.brachy_lib / "media" / "material.dat", 'r') as f_file:
		for f_line in f_file:
			terms = f_line.split()
			if len(terms) == 0:
				continue
			if terms[0] == "medium":
				material_dat_media.append(terms[2])

	if OUTPUT_LATEX_TABLES:
		format_as_latex(material_dat_media)

	main_loop()
