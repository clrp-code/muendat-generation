# built-in modules
from subprocess import run as cmd_run
from subprocess import PIPE

import matplotlib.pyplot as plt
# third party libraries
import numpy as np
import pandas as pd
import seaborn as sns

# user-defined classes
from system_info import sys_info

def overlay_old_and_new_data(
		material_old_new_dict: dict[str, tuple[list[float], list[float],  list[float]]],
		material_name: str
) -> None:
	"""
	Plots both the old and new muen data for `material_name`.
	Saves the plot as a pdf.
	Calling this function will block the program's execution due to the matplotlib .show().
	"""
	energies, muens_old, muens_new = material_old_new_dict[material_name]
	plt.scatter(energies, muens_old, label=r"Old $\mu_{en}$")
	plt.scatter(energies, muens_new, label=r"New $\mu_{en}$")
	plt.savefig(f"old_new_muens_{material_name}.pdf")
	plt.show()

def plot_diffs(
		material_old_new_dict: dict[str, tuple[list[float], list[float], list[float]]]
) -> None:
	"""
	Plots difference between the old and new muen data for all materials.
	Saves the plot as a pdf.
	Calling this function will block the program's execution due to the matplotlib .show().
	"""
	df = pd.DataFrame(columns=['material', 'diff'])
	df['material'] = df['material'].astype(str)
	df['diff'] = df['diff'].astype(float)
	df['diff_std'] = df['diff_std'].astype(float)

	for material_name, (energies, muens_old, muens_new) in material_old_new_dict.items():

		material_df = pd.DataFrame({
			'material': [f"{material_name}"] * len(energies),
			'diff': np.array(muens_new) - np.array(muens_old)
		})

		df = pd.concat([df, material_df], ignore_index=True)

	sns.pointplot(
		data=df,
		x="material",
		y="diff",
		linestyle="none",  # Removes the line connecting the points
		marker="o",  # Point shape
		errorbar="sd",  # Shows standard deviation ('ci' for confidence intervals)
		capsize=0.1,  # Adds caps to the error bars
	)

	plt.savefig(f"diffs_all_materials.pdf")
	plt.show()
