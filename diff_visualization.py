# built-in modules

# third party libraries
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

# user-defined classes

# control variables
PROD = True

def overlay_old_and_new_data(
		material_old_new_dict: dict[str, tuple[list[float], list[float],  list[float]]],
		material_name: str
) -> None:
	"""
	Plots both the old and new muen data for `material_name`.
	Saves the plot as a pdf.
	If diff_visualization.PROD = False, calling this function will block
	the program's execution due to the matplotlib .show().
	"""
	energies, muens_old, muens_new = material_old_new_dict[material_name]
	plt.scatter(energies, muens_old, label=r"Old Data")
	plt.scatter(energies, muens_new, label=r"New Data")
	plt.xscale('log')
	plt.yscale('log')
	plt.xlabel(r"photon energy / MeV")
	plt.ylabel(r"$\mu_{en}/\rho$"+f"({material_name})" + r" / g cm$^{-2}$")
	plt.legend()
	plt.tick_params(top=True, right=True, which='both')
	plt.savefig(f"old_new_muens_{material_name}.pdf")
	if not PROD:
		plt.show()
	plt.close()

	rel_diffs = np.array(muens_new)/np.array(muens_old) - 1
	plt.scatter(energies, 100*rel_diffs)
	plt.xscale('log')
	plt.xlabel(r"photon energy / MeV")
	plt.ylabel(r"relative difference / %")
	plt.gca().yaxis.set_minor_locator(AutoMinorLocator(5))
	plt.tick_params(top=True, right=True, which='both')
	plt.savefig(f"old_new_muens_{material_name}_reldiff.pdf")
	if not PROD:
		plt.show()
	plt.close()

def plot_diffs(
		material_old_new_dict: dict[str, tuple[list[float], list[float], list[float]]]
) -> None:
	"""
	Plots difference between the old and new muen data for all materials.
	Saves the plot as a pdf.
	If diff_visualization.PROD = False, calling this function will block
	the program's execution due to the matplotlib .show().
	"""
	df = pd.DataFrame(columns=['material', 'rel_diff_pct'])
	df['material'] = df['material'].astype(str)
	df['rel_diff_pct'] = df['rel_diff_pct'].astype(float)

	for material_name, (energies, muens_old, muens_new) in material_old_new_dict.items():

		material_df = pd.DataFrame({
			'material': [f"{material_name}"] * len(energies),
			'rel_diff_pct': 100*(np.array(muens_new)/np.array(muens_old) - 1)
		})

		df = pd.concat([df, material_df], ignore_index=True)

	fig, ax = plt.subplots(figsize=(6,10))
	sns.pointplot(
		data=df,
		x="rel_diff_pct",
		y="material",
		linestyle="none",  # Removes the line connecting the points
		marker="o",  # Point shape
		errorbar="sd",  # Shows standard deviation ('ci' for confidence intervals)
		capsize=0.1,  # Adds caps to the error bars
		order=sorted(df["material"].unique())
	)

	plt.tick_params(axis='y', labelsize=7)
	plt.tick_params(top=True, right=True, which='both')
	plt.gca().xaxis.set_minor_locator(AutoMinorLocator(5))
	plt.axvline(x=0, color='k', linestyle='--', linewidth=0.5)

	plt.xlabel(r"average relative difference / %")
	plt.ylabel(r"material")
	plt.subplots_adjust(left=0.3, right=0.95, top=0.95, bottom=0.05)

	plt.savefig(f"diffs_all_materials.pdf")
	if not PROD:
		plt.show()
	plt.close()
