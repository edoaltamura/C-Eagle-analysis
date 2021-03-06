"""
------------------------------------------------------------------
FILE:   save.py
AUTHOR: Edo Altamura
DATE:   20-11-2019
------------------------------------------------------------------
In order to make the data post-processing more manageable, instead
of calculating quantities from the simulations every time, just
compute them once and store them in a hdf5 file.
This process of data reduction level condenses data down to a few KB
or MB and it is possible to transfer it locally for further analysis.
-------------------------------------------------------------------
"""

import sys
import os
import itertools
import time
import numpy as np
import warnings
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib import colors
from matplotlib.patches import Patch

exec(open(os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.path.pardir, 'visualisation', 'light_mode.py'))).read())

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from import_toolkit.simulation import Simulation
from import_toolkit.progressbar import ProgressBar
from import_toolkit._cluster_retriever import redshift_str2num


class SimulationOutput(Simulation):

    # How the directory is structured
    directory_levels = ['simulation_name',
                        'cluster_ID',
                        'redshift',
                        'data.hdf5 && other_outputs.*']

    def __init__(self, simulation_name: str = None, run_dircheck: bool = False):

        super().__init__(simulation_name=simulation_name)
        if run_dircheck:
            self.check_data_structure()

    @ProgressBar()
    def check_data_structure(self):

        if not os.path.exists(os.path.join(self.pathSave, self.simulation_name)):
            os.makedirs(os.path.join(self.pathSave, self.simulation_name))
        length_operation = len(self.clusterIDAllowed) * len(self.redshiftAllowed)
        counter = 0

        for cluster_number, cluster_redshift in itertools.product(self.clusterIDAllowed, self.redshiftAllowed):
            out_path = os.path.join(self.pathSave,
                                    self.simulation_name,
                                    f'halo{self.halo_Num(cluster_number)}',
                                    f'halo{self.halo_Num(cluster_number)}_{cluster_redshift}')

            if (not os.path.exists(out_path) and
                self.sample_completeness[cluster_number, self.redshiftAllowed.index(cluster_redshift)]):
                os.makedirs(out_path)
            yield ((counter + 1) / length_operation)  # Give control back to decorator
            counter += 1

    @staticmethod
    def list_files(startpath):
        for root, dirs, files in os.walk(startpath):
            dirs.sort()
            level = root.replace(startpath, '').count(os.sep)
            indent = ' ' * 4 * (level)
            print('{}{}/'.format(indent, os.path.basename(root)))
            subindent = ' ' * 4 * (level + 1)
            files.sort()
            for f in files:
                print('{}{}'.format(subindent, f))

    def print_directory_tree(self):
        print(self.pathSave)
        self.list_files(os.path.join(self.pathSave, self.simulation_name))

    def dir_tree_to_dict(self, path_):
        file_token = ''
        for root, dirs, files in os.walk(path_):
            tree = {d: self.dir_tree_to_dict(os.path.join(root, d)) for d in dirs}
            tree.update({f: file_token for f in files})
            return tree  # note we discontinue iteration trough os.walk

    @staticmethod
    def draw_pie(dist,
                 xpos,
                 ypos,
                 size,
                 ax=None):
        if ax is None:
            fig, ax = plt.subplots(figsize=(11, 12))

        # for incremental pie slices
        cumsum = np.cumsum(dist)
        cumsum = cumsum / cumsum[-1]
        pie = [0] + cumsum.tolist()
        colors = ['lime', 'red']
        for r1, r2, c in zip(pie[:-1], pie[1:], colors):
            angles = np.linspace(2 * np.pi * r1, 2 * np.pi * r2)
            x = [0] + np.cos(angles).tolist()
            y = [0] + np.sin(angles).tolist()

            xy = np.column_stack([x, y])

            ax.scatter([xpos], [ypos], marker=xy, s=size, facecolor=c, alpha = 0.5)

        return ax



    @ProgressBar()
    def status_plot(self):
        warnings.filterwarnings("ignore")
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111)
        report_matrix = np.zeros((len(self.clusterIDAllowed), len(self.redshiftAllowed)), dtype=np.int)
        length_operation = np.product(report_matrix.shape)
        counter = 0
        for cluster_number, cluster_redshift in itertools.product(self.clusterIDAllowed, self.redshiftAllowed):

            out_path = os.path.join(self.pathSave,
                                    self.simulation_name,
                                    f'halo{self.halo_Num(cluster_number)}',
                                    f'halo{self.halo_Num(cluster_number)}_{cluster_redshift}')

            if self.sample_completeness[cluster_number, self.redshiftAllowed.index(cluster_redshift)]:
                num_of_files = len([name for name in os.listdir(out_path) if os.path.isfile(os.path.join(out_path, name))])
                report_matrix[cluster_number, self.redshiftAllowed.index(cluster_redshift)] = num_of_files
            else:
                report_matrix[cluster_number, self.redshiftAllowed.index(cluster_redshift)] = -1
            yield ((counter + 1) / length_operation)  # Give control back to decorator
            counter += 1



        expected_total_files = 13
        timestr = time.strftime("%d%m%Y-%H%M%S")
        fraction_complete = np.sum(report_matrix[report_matrix>0]) / (np.product(report_matrix.shape) *
                                                                     expected_total_files) * 100

        cmap   = colors.ListedColormap(['white', 'black', 'red', 'orange', 'lime'])
        bounds = [-1, 0, 0.5, 3.5, expected_total_files-0.5, expected_total_files]
        norm   = colors.BoundaryNorm(bounds, cmap.N)
        ax.imshow(report_matrix, interpolation='nearest', cmap=cmap, norm=norm, origin='lower',
                  aspect = report_matrix.shape[1]/report_matrix.shape[0],
                  extent=(0, len(self.redshiftAllowed),
                          0, self.totalClusters))

        patch_1 = Patch(facecolor='black', label='0 files', edgecolor='k', linewidth=1)
        patch_2 = Patch(facecolor='red', label='1 - 3 files', edgecolor='k', linewidth=1)
        patch_3 = Patch(facecolor='orange', label=f'4 - {expected_total_files - 1} files', edgecolor='k', linewidth=1)
        patch_4 = Patch(facecolor='lime', label=f'{expected_total_files} files', edgecolor='k', linewidth=1)
        patch_5 = Patch(facecolor='white', label='Excluded', edgecolor='k', linewidth=1)
        ax.legend(handles=[patch_4, patch_3, patch_2, patch_1, patch_5],
                  loc='upper right',
                  labelspacing=1.5,
                  handlelength=1,
                  fontsize=20,
                  bbox_to_anchor=(1.3, 0.75))

        ax.set_title(f'{self.simulation:s} output status: {fraction_complete:.0f}\% complete \qquad{timestr:s}',
                     size=20)
        ax.set_xlabel(r'redshift', size=20)
        ax.set_ylabel(r'Cluster ID', size=20)
        ax.set_xticks(list(range(0, len(self.redshiftAllowed), 4)))
        redhifts_ticks = [self.redshiftAllowed[i] for i in range(0, len(self.redshiftAllowed), 4)]
        redhifts_ticks = [f"{redshift_str2num(z):.1f}" for z in redhifts_ticks]
        ax.set_xticklabels(redhifts_ticks)
        plt.tight_layout()
        plt.savefig(os.path.join(self.pathSave,
                                 self.simulation_name,
                                 f"{self.simulation_name}_OutputStatusReport_{timestr}.png"), dpi=400)

if __name__ == '__main__':
    for sim in ['celr_e']:
        out = SimulationOutput(simulation_name = sim, run_dircheck = False)
        print(f"{out.simulation:=^100s}")
        out.status_plot()
