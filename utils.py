# built-in modules

# third party libraries

# user-defined classes

def format_as_latex(some_list: list[str], num_columns = 3) -> None:
	"""
	To create egs_brachy_user_manual.pdf tables, it helps to automate the LaTeX table generation
	"""

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
	one_third = len(trimmed_list) // num_columns  # called one_third because the default is ncol = 3
	for idx in range(one_third+1):
		out_str = ""
		for col in range(num_columns):
			jdx = col * one_third + idx
			if jdx < length:
				name = r"\_".join(trimmed_list[jdx].split('_'))
				name = r"\%".join(name.split('%'))
				out_str += f" {name} &"

		print(f"{out_str[:-1]} \\\\")