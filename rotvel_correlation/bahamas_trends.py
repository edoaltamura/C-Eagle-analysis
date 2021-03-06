import os, sys
import itertools
import warnings
from typing import List
import numpy as np
import slack
import socket

# Graphics packages
import matplotlib
matplotlib.use('Agg')
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
plt.style.use("mnras.mplstyle")

# Internal packages
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
import utils

def save_plot(filepath: str, to_slack: bool = False, **kwargs) -> None:
	"""
	Function to parse the plt.savefig method and send the file to a slack channel.
	:param filepath: The path+filename+extension where to save the figure
	:param to_slack: Gives the option to send the the plot to slack
	:param kwargs: Other kwargs to parse into the plt.savefig
	:return: None
	"""
	plt.savefig(filepath, **kwargs)
	if to_slack:
		print(
				"[+] Forwarding to the `#personal` Slack channel",
				f"\tDir: {os.path.dirname(filepath)}",
				f"\tFile: {os.path.basename(filepath)}",
				sep='\n'
		)
		slack_token = 'xoxp-452271173797-451476014913-1101193540773-57eb7b0d416e8764be6849fdeda52ce8'
		slack_msg = f"Host: {socket.gethostname()}\nDir: {os.path.dirname(filepath)}\nFile: {os.path.basename(filepath)}"
		try:
			# Send files to Slack: init slack client with access token
			client = slack.WebClient(token=slack_token)
			client.files_upload(file=filepath, initial_comment=slack_msg, channels='#personal')
		except:
			warnings.warn("[-] Failed to broadcast plot to Slack channel.")

def median_plot(axes: plt.Axes, x: np.ndarray, y: np.ndarray,  **kwargs):

	perc84 = Line2D([], [], color='k', marker='^', linewidth=1, linestyle='-', markersize=3, label=r'$84^{th}$ percentile')
	perc50 = Line2D([], [], color='k', marker='o', linewidth=1, linestyle='-', markersize=3, label=r'median')
	perc16 = Line2D([], [], color='k', marker='v', linewidth=1, linestyle='-', markersize=3, label=r'$16^{th}$ percentile')
	legend = axes.legend(handles=[perc84, perc50, perc16], loc='lower right', handlelength=2)
	axes.add_artist(legend)
	data_plot = utils.medians_2d(x, y, **kwargs)
	axes.errorbar(data_plot['median_x'], data_plot['median_y'], yerr=data_plot['err_y'],
	              marker='o', ms=2, alpha=1, linestyle='-', capsize=0, linewidth=0.5)
	axes.errorbar(data_plot['median_x'], data_plot['percent16_y'], yerr=data_plot['err_y'],
	              marker='v', ms=2, alpha=1, linestyle='-', capsize=0, linewidth=0.5)
	axes.errorbar(data_plot['median_x'], data_plot['percent84_y'], yerr=data_plot['err_y'],
	              marker='^', ms=2, alpha=1, linestyle='-', capsize=0, linewidth=0.5)

def kde_plot(axes: plt.Axes, x: np.ndarray, y: np.ndarray, **kwargs):

	kde_results = utils.kde_2d(x, y, **kwargs)
	clevels = axes.contourf(*kde_results, 10, cmap='YlGn_r')

	# Delete outer levels
	for level in clevels.collections:
		for kp, path in reversed(list(enumerate(level.get_paths()))):
			verts = path.vertices  # (N,2)-shape array of contour line coordinates
			diameter = np.max(verts.max(axis=0) - verts.min(axis=0))
			dataset_diameter = max([(x.max()-x.min()), (y.max()-y.min())])
			if diameter > 0.75*dataset_diameter:
				del (level.get_paths()[kp])

	# Identify points within contours
	inside = np.full_like(x, False, dtype=bool)
	for level in clevels.collections:
		for kp, path in reversed(list(enumerate(level.get_paths()))):
			inside |= path.contains_points(tuple(zip(*(x,y))))
	ax.scatter(x[~inside], y[~inside], marker='.', color='g', s=2, alpha=0.1)

	# # Count points within each level
	# points_in_level = []
	# inside = np.full_like(x, False, dtype=bool)
	# for level in clevels.collections:
	# 	for kp, path in reversed(list(enumerate(level.get_paths()))):
	# 		inside |= path.contains_points(tuple(zip(*(x,y))))
	# 		points_in_level.append(len(inside[inside==True]))
	# points_in_level.append(len(x))
	#
	# # Plot colorbar
	# divider = make_axes_locatable(axes)
	# cax = divider.append_axes('right', size='5%', pad=0.05)
	# cbar = plt.gcf().colorbar(clevels, cax=cax, orientation='vertical')
	# N_levels = len(points_in_level)
	# kde_ticks = np.linspace(np.min(kde_results[2]), np.max(kde_results[2]), N_levels+1)
	# cbar.ax.set_yticks(kde_ticks[::2])
	# cbar.ax.set_yticklabels([f"{n/len(x):2.2f}" for n in points_in_level[::2][::-1]])
	# cbar.ax.set_ylabel(r"$\frac{n}{N}$", rotation=0, fontsize=13, labelpad=15)



def snap_label(axes: plt.Axes, redshift: str, aperture: int) -> None:
	label = f"BAHAMAS$^\mathrm{{h}}$\n$z={utils.redshift_str2num(redshift):2.2f}$\n$R_\\mathrm{{aperture}}=${utils.aperture_labels[aperture]}"
	axes.text(0.97, 0.97, label, transform=axes.transAxes, horizontalalignment='right', verticalalignment='top')


if __name__ == '__main__':
	#-----------------------------------------------------------------
	redshift = 'z001p750'
	aperture = 7
	x_dataset = 'm500'
	y_dataset = 'a_l'
	axscales = ['log', 'linear']
	# Remember to change the dataset slicing as appropriate to the dataset
	#-----------------------------------------------------------------
	x = utils.read_snap_output(redshift, apertureID=aperture, dataset=x_dataset)
	y = np.abs(np.cos(2*np.pi/180*utils.read_snap_output(redshift, apertureID=aperture, dataset=y_dataset)))

	fig = plt.figure()
	size = fig.get_size_inches()
	size[1] *= 3
	fig.set_size_inches(size[0], size[1], forward=True)
	figname = f'bahamas_hyd_alignment_{redshift}.png'


	ax = fig.add_subplot(411)
	x_dat = x
	y_dat = y[:,0,0]
	ptype = (0,0)
	# ax.set_ylim(0, 1)
	ax.set_xscale(axscales[0])
	ax.set_yscale(axscales[1])
	ax.set_ylabel("|cos("+utils.datasets_names[y_dataset]+")|")
	# plabel = f"$({utils.get_label_between(ax.get_ylabel())})$ = ({utils.partType_labels[ptype[0]]}, {utils.partType_labels[ptype[1]]})"
	# ax.text(0.03, 0.03, plabel, transform=ax.transAxes, horizontalalignment='left', verticalalignment='bottom')
	# plt.axhline(90, color='grey', linestyle='-')
	# ax.set_yticks(np.arange(0, 210, 30))
	kde_plot(ax, x_dat, y_dat, axscales = axscales, gridbins=400)
	median_plot(ax, x_dat, y_dat, axscales = axscales, binning_method = 'equalnumber')
	snap_label(ax, redshift, aperture)

	plt.setp(ax.get_xticklabels(), visible=False)

	ax = fig.add_subplot(412, sharex=ax)
	x_dat = x
	y_dat = y[:,1,1]
	ptype = (1, 1)
	# ax.set_ylim(0, 1)
	ax.set_xscale(axscales[0])
	ax.set_yscale(axscales[1])
	ax.set_ylabel("|cos("+utils.datasets_names[y_dataset]+")|")
	# plabel = f"$({utils.get_label_between(ax.get_ylabel())})$ = ({utils.partType_labels[ptype[0]]}, {utils.partType_labels[ptype[1]]})"
	# ax.text(0.03, 0.03, plabel, transform=ax.transAxes, horizontalalignment='left', verticalalignment='bottom')
	# plt.axhline(90, color='grey', linestyle='-')
	# ax.set_yticks(np.arange(0, 210, 30))
	kde_plot(ax, x_dat, y_dat, axscales = axscales, gridbins=400)
	median_plot(ax, x_dat, y_dat, axscales = axscales, binning_method = 'equalnumber')

	# remove last tick label for the second subplot
	yticks = ax.yaxis.get_major_ticks()
	yticks[-1].label1.set_visible(False)
	plt.setp(ax.get_xticklabels(), visible=False)

	ax = fig.add_subplot(413, sharex=ax)
	x_dat = x
	y_dat = y[:, 2, 2]
	ptype = (2, 2)
	# ax.set_ylim(0, 1)
	ax.set_xscale(axscales[0])
	ax.set_yscale(axscales[1])
	ax.set_ylabel("|cos("+utils.datasets_names[y_dataset]+")|")
	# plabel = f"$({utils.get_label_between(ax.get_ylabel())})$ = ({utils.partType_labels[ptype[0]]}, {utils.partType_labels[ptype[1]]})"
	# ax.text(0.03, 0.03, plabel, transform=ax.transAxes, horizontalalignment='left', verticalalignment='bottom')
	# plt.axhline(90, color='grey', linestyle='-')
	# ax.set_yticks(np.arange(0, 210, 30))
	kde_plot(ax, x_dat, y_dat, axscales=axscales, gridbins=400)
	median_plot(ax, x_dat, y_dat, axscales=axscales, binning_method='equalnumber')

	# remove last tick label for the second subplot
	yticks = ax.yaxis.get_major_ticks()
	yticks[-1].label1.set_visible(False)
	plt.setp(ax.get_xticklabels(), visible=False)

	ax = fig.add_subplot(414, sharex=ax)
	x_dat = x
	y_dat = y[:,3,3]
	ptype = (3, 3)
	# ax.set_ylim(0, 1)
	ax.set_xscale(axscales[0])
	ax.set_yscale(axscales[1])
	ax.set_xlabel(utils.datasets_names[x_dataset])
	ax.set_ylabel("|cos("+utils.datasets_names[y_dataset]+")|")
	# plabel = f"$({utils.get_label_between(ax.get_ylabel())})$ = ({utils.partType_labels[ptype[0]]}, {utils.partType_labels[ptype[1]]})"
	# ax.text(0.03, 0.03, plabel, transform=ax.transAxes, horizontalalignment='left', verticalalignment='bottom')
	# plt.axhline(90, color='grey', linestyle='-')
	# ax.set_yticks(np.arange(0, 210, 30))
	kde_plot(ax, x_dat, y_dat, axscales = axscales, gridbins=400)
	median_plot(ax, x_dat, y_dat, axscales = axscales, binning_method = 'equalnumber')

	# remove last tick label for the second subplot
	yticks = ax.yaxis.get_major_ticks()
	yticks[-1].label1.set_visible(False)

	fig.subplots_adjust(hspace=0)
	fig.tight_layout()
	save_plot(os.path.join(utils.basepath, figname), to_slack=True, dpi=400)