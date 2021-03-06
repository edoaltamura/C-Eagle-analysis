import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib.gridspec as gridspec
import matplotlib.colors as colors
import matplotlib.patches as patches

from visualisation import map_plot_parameters as plotpar
from obsolete import map_synthetizer as mapgen
import gas_fractions_gridSpec_calculator as data

from os.path import exists
from os import makedirs
from itertools import count
from matplotlib.ticker import NullFormatter
from matplotlib.colorbar import Colorbar

# Define selection
def selection(default = True, set_dict = None):
	if default:
		temp_dict = {'SELECT_R_MIN': 0,
					  'SELECT_R_MAX': 5,

					  'SELECT_M_MIN': 10 ** 12,
					  'SELECT_M_MAX': 10 ** 14.5,

					  'SELECT_Fg_MIN': 0.01,
					  'SELECT_Fg_MAX': 0.25,

					  'SELECT_Vr_MIN': 0,
					  'SELECT_Vr_MAX': 100,

					  'SELECT_MV_MIN': -np.inf,
					  'SELECT_MV_MAX': np.inf}

	else:
		temp_dict = set_dict
	return temp_dict

# Release constraints module
def release_constraints(array):
	for constraint in array:
		if constraint == 'R':
			selec_dict['SELECT_R_MIN'] = 0
			selec_dict['SELECT_R_MAX'] = np.inf
		if constraint == 'M':
			selec_dict['SELECT_M_MIN'] = 0
			selec_dict['SELECT_M_MAX'] = np.inf
		if constraint == 'Fg':
			selec_dict['SELECT_Fg_MIN'] = -np.inf
			selec_dict['SELECT_Fg_MAX'] = np.inf
		if constraint == 'Vr':
			selec_dict['SELECT_Vr_MIN'] = -np.inf
			selec_dict['SELECT_Vr_MAX'] = np.inf
		if constraint == 'MV':
			selec_dict['SELECT_MV_MIN'] = -np.inf
			selec_dict['SELECT_MV_MAX'] = np.inf

# Check file uniqueness [unused in this version]
def unique_file(basename, ext):
	actualname = "%s.%s" % (basename, ext)
	c = count()
	while exists(actualname):
		actualname = "%s (%d).%s" % (basename, next(c), ext)
	return actualname

# Compute subfind subhalo catalog with possibility to set own selection dictionary (use default_select = False)
def compute_catalog(halo_number, redshift, projection, output = "None", default_select = True, set_select = None):
	# DATA
	global data_dict
	data_dict = {'index': data.std_HighRes_index(halo_number, redshift),
				 'H': halo_number * np.ones_like(data.std_HighRes_index(halo_number, redshift)),
				 # Index catalog from the hdf5 file (selected for high res region)
				 'R': data.std_r(halo_number, redshift),  # Units: physical R/R_200
				 'M': data.std_m_tot(halo_number, redshift),  # Units: physical solar masses
				 'Fg': data.std_gasFrac(halo_number, redshift),
				 'Vr': data.std_Vr(halo_number, redshift),  # Remember: this is a tuple of x,y,z coordinates
				 'MV': data.std_MVr(halo_number, redshift)}  # Remember: this is a tuple of x,y,z coordinates

	thirdaxis = [2, 1, 0]
	data_dict['Vr'] = data_dict['Vr'][thirdaxis[projection]]
	data_dict['MV'] = data_dict['MV'][thirdaxis[projection]]

	# SELECTION
	global selec_dict
	selec_dict = selection(default_select, set_select)

	release_constraints(['MV', 'R', 'Vr', 'Fg'])

	# Create catalogue of sgn for markers on SZ maps
	index = np.where(
		(data_dict['R'] > selec_dict['SELECT_R_MIN']) & (data_dict['R'] < selec_dict['SELECT_R_MAX']) &
		(data_dict['M'] > selec_dict['SELECT_M_MIN']) & (data_dict['M'] < selec_dict['SELECT_M_MAX']) &
		(data_dict['Fg'] > selec_dict['SELECT_Fg_MIN']) & (data_dict['Fg'] < selec_dict['SELECT_Fg_MAX']) &
		((data_dict['Vr'] > selec_dict['SELECT_Vr_MIN']) & (data_dict['Vr'] < selec_dict['SELECT_Vr_MAX']) |
		 (data_dict['Vr'] < -selec_dict['SELECT_Vr_MIN']) & (data_dict['Vr'] > -selec_dict['SELECT_Vr_MAX'])) &
		(data_dict['MV'] > selec_dict['SELECT_MV_MIN']) & (data_dict['MV'] < selec_dict['SELECT_MV_MAX'])
	)[0]

	global catalog_dict
	catalog_dict = {'H':0, 'I': 0,	'R': 0,	'M': 0,	'Fg': 0, 'Vr': 0, 'MV': 0}
	catalog_dict['H'] = data_dict['H'][index].astype(np.int32)
	catalog_dict['I'] = data_dict['index'][index].astype(np.int32)
	catalog_dict['R'] = data_dict['R'][index]
	catalog_dict['M'] = data_dict['M'][index]
	catalog_dict['Fg'] = data_dict['Fg'][index]
	catalog_dict['Vr'] = data_dict['Vr'][index]
	catalog_dict['MV'] = data_dict['MV'][index]

	# Export the full catalog with data
	if output.lower() == "save":
		dir_name = 'Subfind-Selection'
		outfile = 'sg_catalog_halo' + str(halo_number) + '_z' + str(redshift).replace(".", "") + '_proj' + str(projection) + '.npy'
		if not exists(dir_name): makedirs(dir_name)
		if os.path.isfile(dir_name + '//' + outfile): os.remove(dir_name + '//' + outfile)
		np.save(dir_name + '//' + outfile, catalog_dict)

	elif output.lower() == "return":
		return catalog_dict

	elif output.lower() == "none":
		pass

	else: print("Error: Invalid request\n")

def ltx_export(halo_number, redshift, projection):
	Panda_catalog = pd.DataFrame.from_dict(catalog_dict, orient='index')

	Panda_catalog = Panda_catalog.transpose()
	LaTeX_catalog = Panda_catalog.to_latex(index=True, col_space=3, multicolumn=True, multicolumn_format='c',
										   header=True, bold_rows=True)
	# print(LaTeX_catalog)

	Panda_boundaries = pd.DataFrame.from_dict(selec_dict, orient='index')
	# Panda_boundaries = Panda_boundaries.transpose()
	# Panda_boundaries.applymap(lambda x:exp_tex(x))
	LaTeX_boundaries = Panda_boundaries.to_latex(index=True, col_space=3, multicolumn=True, multicolumn_format='c',
												 header=True, bold_rows=True)

	beginningtex = """\\documentclass{report}[12pt]
		\\usepackage{booktabs}
		\\usepackage{siunitx}
		\\begin{document}
		\\begin{center}
		"""
	endtex = """\\end{center}
		\\end{document}"""

	dir_name = 'Subfind-Selection'
	f = open(dir_name + '//sg_catalog_halo' + str(halo_number) + '_z' + str(redshift).replace(".", "") + '_proj' + str(projection) + '.tex', 'w')
	f.write(beginningtex)
	f.write(LaTeX_boundaries)
	f.write(LaTeX_catalog)
	f.write(endtex)
	f.close()

def render_figure(halo_number, redshift, projection, output = "Show"):
	plotpar.set_defaults_plot()
	nullfmt = NullFormatter()
	fig = plt.figure(1, figsize=(10, 13))

	# Now, create the gridspec structure, as required
	gs = gridspec.GridSpec(ncols=3, nrows=7,
						   height_ratios=[0.05, 1, 0.5, 0.7, 0.05, 1, 0.5],
						   width_ratios=[1, 1, 0.5])

	# 3 rows, 4 columns, each with the required size ratios.
	# Also make sure the margins and spacing are apropriate

	gs.update(left=0.05, right=0.95, bottom=0.08, top=0.93, wspace=0.08, hspace=0.08)

	# Note: I set the margins to make it look good on my screen ...
	# BUT: this is irrelevant for the saved image, if using bbox_inches='tight'in savefig !

	# Note: Here, I use a little trick. I only have three vertical layers of plots :
	# a scatter plot, a histogram, and a line plot. So, in principle, I could use a 3x3 structure.
	# However, I want to have the histogram 'closer' from the scatter plot than the line plot.
	# So, I insert a 4th layer between the histogram and line plot,
	# keep it empty, and use its thickness (the 0.2 above) to adjust the space as required.

	selection_color = 'coral'
	# selection_color = 'lime'
	colormap = 'YlGnBu_r'
	alpha_select = 0.1

	# LABELS
	label_n = r'$n_{sub}$'
	label_M = r'$M/M_\odot$'
	label_R = r'$R/R_{200}$'
	label_f = r'$f_{g}$'
	label_v = r'$v_{z}/\mathrm{(km\ s^{-1})}$'

	# GRIDS & NBINS
	grid_on = False

	# loop over plots
	for j in [0, 4]:
		for i in [0, 1]:

			print('Block started')

			if i == 0 and j == 0:
				x = data_dict['R']
				y = data_dict['Fg']
				SELECT_x_min, SELECT_x_max = selec_dict['SELECT_R_MIN'], selec_dict['SELECT_R_MAX']
				SELECT_y_min, SELECT_y_max = selec_dict['SELECT_Fg_MIN'], selec_dict['SELECT_Fg_MAX']
			if i == 1 and j == 0:
				x = data_dict['M']
				y = data_dict['Fg']
				SELECT_x_min, SELECT_x_max = selec_dict['SELECT_M_MIN'], selec_dict['SELECT_M_MAX']
				SELECT_y_min, SELECT_y_max = selec_dict['SELECT_Fg_MIN'], selec_dict['SELECT_Fg_MAX']
			if i == 0 and j == 4:
				x = data_dict['R']
				y = data_dict['Vr']
				SELECT_x_min, SELECT_x_max = selec_dict['SELECT_R_MIN'], selec_dict['SELECT_R_MAX']
				SELECT_y_min, SELECT_y_max = selec_dict['SELECT_Vr_MIN'], selec_dict['SELECT_Vr_MAX']
			if i == 1 and j == 4:
				x = data_dict['M']
				y = data_dict['Vr']
				SELECT_x_min, SELECT_x_max = selec_dict['SELECT_M_MIN'], selec_dict['SELECT_M_MAX']
				SELECT_y_min, SELECT_y_max = selec_dict['SELECT_Vr_MIN'], selec_dict['SELECT_Vr_MAX']

			x_min_LIN, x_max_LIN = np.min(x), np.max(x)
			x_min_LOG, x_max_LOG = np.log10(x_min_LIN), np.log10(x_max_LIN)
			y_min_LIN, y_max_LIN = np.min(y), np.max(y)
			if j == 0: y_min_LIN, y_max_LIN = 0, 0.3

			# First, the scatter plot
			ax1 = fig.add_subplot(gs[j + 1, i])
			print('\tComputing 2dhist \t\t (%1i, %1i)' % (j + 1, i))
			# # Get the optimal number of bins based on knuth_bin_width
			# N_xbins = int((np.max(x)-np.min(x))/knuth_bin_width(x)) + 1
			# N_ybins = int((np.max(y)-np.min(y))/knuth_bin_width(y)) + 1
			N_xbins = 50
			N_ybins = N_xbins
			bins_LOG = np.logspace(x_min_LOG, x_max_LOG, num=N_xbins)
			bins_LIN = np.linspace(y_min_LIN, y_max_LIN, num=N_ybins)
			Cx, Cy = mapgen.bins_meshify(x, y, bins_LOG, bins_LIN)
			count = mapgen.bins_evaluate(x, y, bins_LOG, bins_LIN, weights=None)
			norm = colors.LogNorm()
			plt1 = ax1.pcolor(Cx, Cy, count, cmap=colormap, norm=norm)
			ax1.grid(grid_on)
			ax1.set_xlim([x_min_LIN, x_max_LIN])
			ax1.set_ylim([y_min_LIN, y_max_LIN])
			ax1.set_xscale('log')
			ax1.set_yscale('linear')
			ax1.set_xlabel(r' ')  # Force this empty !
			ax1.xaxis.set_major_formatter(nullfmt)
			ax1.set_ylabel(label_f)
			if j == 4:
				ax1.axhspan(-SELECT_y_max, -SELECT_y_min, alpha=alpha_select, color=selection_color)
				rect2 = patches.Rectangle((SELECT_x_min, -SELECT_y_max), SELECT_x_max - SELECT_x_min,
										  -SELECT_y_min + SELECT_y_max, linewidth=1.5, edgecolor='r', facecolor='none')
				ax1.add_patch(rect2)

			ax1.axvspan(SELECT_x_min, SELECT_x_max, alpha=alpha_select, color=selection_color)
			ax1.axhspan(SELECT_y_min, SELECT_y_max, alpha=alpha_select, color=selection_color)
			rect = patches.Rectangle((SELECT_x_min, SELECT_y_min), SELECT_x_max - SELECT_x_min,
									 SELECT_y_max - SELECT_y_min, linewidth=1.5, edgecolor='r', facecolor='none')
			ax1.add_patch(rect)
			if j == 0:
				ax1.set_ylabel(label_f)
			elif j == 4:
				ax1.set_ylabel(label_v)

			# Colorbar
			cbax = fig.add_subplot(gs[j, i])
			print('\tComputing colorbar \t\t (%1i, %1i)' % (j, i))
			cb = Colorbar(ax=cbax, mappable=plt1, orientation='horizontal', ticklocation='top')
			cb.set_label(label_n, labelpad=10)
			trig_vertical_hist = 0
			# VERTICAL HISTOGRAM
			if i != 0:
				ax1v = fig.add_subplot(gs[j + 1, i + 1])
				print('\tComputing vert hist \t (%1i, %1i)' % (j + 1, i + 1))
				ax1v.hist(y, bins=bins_LIN, orientation='horizontal', color='k', histtype='step')
				ax1v.hist(y, bins=bins_LIN, orientation='horizontal', color='red', histtype='step', cumulative=-1)
				ax1v.set_yticks(ax1.get_yticks())  # Ensures we have the same ticks as the scatter plot !
				ax1v.set_xlabel(label_n)
				ax1v.tick_params(labelleft=False)
				ax1v.set_ylim(ax1.get_ylim())
				ax1v.set_xscale('log')
				ax1v.set_yscale('linear')
				ax1v.grid(grid_on)
				ax1v.axhspan(SELECT_y_min, SELECT_y_max, alpha=alpha_select, color=selection_color)
				if j == 4:
					ax1v.axhspan(-SELECT_y_max, -SELECT_y_min, alpha=alpha_select, color=selection_color)

				ax1.yaxis.set_major_formatter(nullfmt)
				ax1.set_ylabel('')
				trig_vertical_hist = 1

			# Percentiles
			percents = [15.9, 50, 84.1]
			percent_str = [r'$16\%$', r'$50\%$', r'$84\%$']
			clr = ['orange', 'blue', 'green']
			percent_ticks = np.percentile(y, percents)
			if trig_vertical_hist:
				percent_str = np.flipud(percent_str)
				clr = np.flipud(clr)
				ax1v_TWIN = ax1v.twinx()
				ax1v_TWIN.set_ylim(ax1.get_ylim())
				ax1v_TWIN.tick_params(axis='y', which='both', labelleft='off', labelright='on')
				ax1v_TWIN.set_yticks(percent_ticks)
				ax1v_TWIN.set_yticklabels(percent_str)
				for percent_tick, c, tick in zip(percent_ticks, clr, ax1v_TWIN.yaxis.get_major_ticks()):
					tick.label1.set_color(c)
					ax1v_TWIN.axhline(y=percent_tick, color=c, linestyle='--')
				percent_str = np.flipud(percent_str)
				clr = np.flipud(clr)

			# HORIZONTAL HISTOGRAM
			ax1h = fig.add_subplot(gs[j + 2, i])
			print('\tComputing horiz hist \t (%1i, %1i)' % (j + 2, i))
			ax1h.hist(x, bins=bins_LOG, orientation='vertical', color='k', histtype='step')
			ax1h.hist(x, bins=bins_LOG, orientation='vertical', color='red', histtype='step', cumulative=True)
			ax1h.set_xticks(ax1.get_xticks())  # Ensures we have the same ticks as the scatter plot !
			ax1h.set_xlim(ax1.get_xlim())
			if i == 0:
				ax1h.set_xlabel(label_R)
				ax1h.set_ylabel(label_n)
			elif i == 1:
				ax1h.set_xlabel(label_M)
				ax1h.tick_params(labelleft=False)
				ax1h.set_ylabel('')
			ax1h.set_xscale('log')
			ax1h.set_yscale('log')
			ax1h.grid(grid_on)
			ax1h.axvspan(SELECT_x_min, SELECT_x_max, alpha=alpha_select, color=selection_color)
			percent_ticks = np.percentile(x, percents)
			for i in range(len(percents)): ax1h.axvline(x=percent_ticks[i], color=clr[i], linestyle='--')

			print('Block completed\n')

	if output.lower() == 'show':
		fig.show()

	elif output.lower() == 'save':
		dir_name = 'Subfind-Selection'
		if not exists(dir_name): makedirs(dir_name)
		save_name = 'selection-phase-space_halo' + str(halo_number) + '_z' + str(redshift).replace(".", "") + '_proj' + str(projection) + '.pdf'
		fig.savefig(dir_name + '//' + save_name,
					dpi=None, facecolor='w', edgecolor='w',
					orientation='portrait', papertype=None, format=None,
					transparent=False, bbox_inches='tight', pad_inches=0.1,
					frameon=None)

	elif output.lower() == 'none':
		pass

	else: print("Error: Invalid request")

def call(rank):
	halo_number = rank
	redshift = 0.57

	for p in [0]:
		compute_catalog(halo_number, redshift, p, output='save')
		ltx_export(halo_number, redshift, p)
		render_figure(halo_number, redshift, p, output='save')

# **************************************************************************************************
# MPI implementation

# $$$ CMD: >> mpiexec -n <number-of-threads> python <file>
# $$$ CMD: >> mpiexec -n 10 python map_kSZ-tSZ-M_intensity.py

if __name__ == "__main__":
	from mpi4py import MPI
	comm = MPI.COMM_WORLD
	size = comm.Get_size()
	rank = comm.Get_rank()
	print('process:', rank)
	call(rank)
