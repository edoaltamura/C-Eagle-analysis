"""
------------------------------------------------------------------
FILE:   rotvel_correlation/align_angles.py
AUTHOR: Edo Altamura
DATE:   15-03-2020
------------------------------------------------------------------
The save python package generates partial raw data from the simulation
data. The pull.py file accesses and reads these data and returns
then in a format that can be used for plotting, further processing
etc.
-------------------------------------------------------------------
"""

import numpy as np
import sys
import os.path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from sklearn.utils import resample
from typing import List, Dict, Tuple
import itertools



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from import_toolkit.cluster import Cluster
from import_toolkit.simulation import Simulation
from import_toolkit._cluster_retriever import redshift_str2num
from read import pull

class CorrelationMatrix(pull.FOFRead):

    def __init__(self, cluster: Cluster):

        super().__init__(cluster)

    def get_data(self):
        return self.pull_rot_vel_alignment_angles()

    def get_apertures(self):
        return self.pull_apertures()

    @staticmethod
    def get_percentiles(data: np.ndarray, percentiles: list = [15.9, 50, 84.1]) -> np.ndarray:
        data = np.asarray(data)
        return np.array([np.percentile(data, percent, axis=0) for percent in percentiles])

    def bootstrap(self, data: np.ndarray, n_iterations: int = 1e3) -> Dict[str, Tuple[float, float]]:
        """
        Class method to compute the median/percentile statistics of a 1D dataset using the
        bootstrap resampling. The bootstrap allows to compute the dispersion of values in the
        computed median/percentiles.
        The method checks for the input dimensionality, then creates many realisations of the
        initial dataset while resampling & replacing elements. The random seed is controlled
        by a for loop of n_iterations (default 1000) iterations. It then computes the percentiles
        for each realisation of the dataset and pushes the percentile results into a master stats
        array.
        From this master array of shape (n_iterations, 3), where all percentiles are gathered,
        the mean and standard deviations are computed for each type of percentile and returned
        in the form of a dictionary: the 3 percentiles with quoted mean and std.

        :param data: expect 1D numpy array
            Lists are also handled, provided they make it though the static typing condition.

        :param n_iterations: expect int (default det to 1000)
            The number of realisations for the bootstrap resampling. Recommended to be > 1e3.

        :return:  Dict[str, Tuple[float, float]]
            The mean and standard deviation (from the bootstrap sample), quoted for each
            percentile and median.
        """
        data = np.asarray(data)
        assert data.ndim is 1, f"Expected `data` to have dimensionality 1, got {data.ndim}."
        stats_resampled = np.zeros((0, 3), dtype=np.float)

        for seed in range(n_iterations):
            data_resampled = resample(data, replace=True, n_samples=len(data), random_state=seed)
            stats = self.get_percentiles(data_resampled, percentiles=[15.9, 50, 84.1])
            stats_resampled = np.concatenate((stats_resampled, [stats]), axis=0)

        stats_resampled_MEAN = np.mean(stats_resampled, axis=0)
        stats_resampled_STD  = np.std(stats_resampled, axis=0)
        bootstrap_stats = {
            'percent16': (stats_resampled_MEAN[0], stats_resampled_STD[0]),
            'median50' : (stats_resampled_MEAN[1], stats_resampled_STD[1]),
            'percent84': (stats_resampled_MEAN[2], stats_resampled_STD[2])
        }

        return bootstrap_stats

    def plot_matrix(self, angle_matrix, apertures):

        fig = plt.figure(figsize=(12, 12))
        ax = fig.add_subplot(111)

        im = ax.imshow(angle_matrix, cmap='Set3_r', vmin=0, vmax=180, origin='lower')
        # Manipulate the colorbar on the side
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3%", pad=0.1)
        cbar = fig.colorbar(im, cax=cax, ticks=np.linspace(0, 180, 13))
        cbar.ax.minorticks_off()
        cbar.ax.set_ylabel(r'$\Delta \theta$ \quad [degrees]', rotation=270, size=25, labelpad=30)

        x_labels = [
            r'$\mathbf{\widehat{v_{pec}}}$',
            r'$\mathbf{\widehat{L}}$',
            r'$\mathbf{\widehat{v_{pec}}}^{(gas)}$',
            r'$\mathbf{\widehat{v_{pec}}}^{(DM)}$',
            r'$\mathbf{\widehat{v_{pec}}}^{(stars)}$',
            r'$\mathbf{\widehat{v_{pec}}}^{(BH)}$',
            r'$\mathbf{\widehat{L}}^{(gas)}$',
            r'$\mathbf{\widehat{L}}^{(DM)}$',
            r'$\mathbf{\widehat{L}}^{(stars)}$',
            r'$\mathbf{\widehat{L}}^{(BH)}$'
        ]

        ticks_major = np.arange(0, len(x_labels), 1)
        ticks_minor = np.arange(-0.5, len(x_labels), 1)
        ax.set_xticks(ticks_major, minor=False)
        ax.set_yticks(ticks_major, minor=False)
        ax.set_xticks(ticks_minor, minor=True)
        ax.set_yticks(ticks_minor, minor=True)
        ax.set_xticklabels(x_labels, rotation = 90)
        ax.set_yticklabels(x_labels)

        # Compute percentiles
        percentiles = self.get_percentiles(angle_matrix)
        percent16 = percentiles[0]
        median50 = percentiles[1]
        percent84 = percentiles[2]

        # Loop over data dimensions and create text annotations.
        for i in range(len(x_labels)):
            for j in range(len(x_labels)):
                if i is not j:
                     ax.text(j, i, r"${:.2f}^{{+{:.2f}}}_{{-{:.2f}}}$".format(
                                median50[i, j],
                                percent84[i, j] - median50[i, j],
                                median50[i, j] - percent16[i, j]),
                                ha="center", va="center", color="k", size = 12)

        ax.set_title(r"Aperture = {:.2f}".format(apertures) + r"\ $R_{500\ true}$", size = 25)
        ax.grid(b = True, which='minor',color='w', linestyle='-', linewidth=10, alpha = 1)

        ax.tick_params(which='minor', length=0, color='w')
        ax.tick_params(which='major', length=0, color='w')
        for pos in ['top', 'bottom', 'right', 'left']:
            ax.spines[pos].set_edgecolor('w')

        fig.tight_layout()

class TrendZ:

    # Inherit methods from the CorrelationMatrix class
    get_percentiles = staticmethod(CorrelationMatrix.get_percentiles)
    bootstrap = CorrelationMatrix.bootstrap

    def __init__(self):
        pass

    def get_apertures(self, cluster: Cluster):
        read = pull.FOFRead(cluster)
        return read.pull_apertures()

    def plot_z_trends(self,
                      simulation_name: str = None,
                      aperture_id: int = 10):

        sim = Simulation(simulation_name=simulation_name)
        aperture_id_str = f'Aperture {aperture_id}'
        aperture_float = aperture_id
        print(f"{sim.simulation:=^100s}")
        print(f"{aperture_id_str:^100s}\n")
        print(f"{'':<30s} {' process ID ':^25s} | {' halo ID ':^15s} | {' halo redshift ':^20s}\n")

        angle_master = np.zeros((len(sim.clusterIDAllowed), len(sim.redshiftAllowed)), dtype=np.float)
        z_master = np.array([redshift_str2num(z) for z in sim.redshiftAllowed])

        iterator = itertools.product(sim.clusterIDAllowed, sim.redshiftAllowed)
        for process_n, (halo_id, halo_z) in enumerate(list(iterator)[0:200]):
            print(f"{'Processing...':<30s} {process_n:^25d} | {halo_id:^15d} | {halo_z:^20s}")
            cluster = Cluster(simulation_name=simulation_name, clusterID=halo_id, redshift=halo_z)
            read = pull.FOFRead(cluster)
            angle = read.pull_rot_vel_angle_between('Total_angmom', 'Total_ZMF')[aperture_id]
            angle_master[sim.redshiftAllowed.index(halo_z)][halo_id] = angle

            if process_n is 0:
                aperture_float = self.get_apertures(cluster)[aperture_id]/cluster.r500

        fig = plt.figure(figsize=(12, 12))
        ax = fig.add_subplot(111)

        print(angle_master.shape)
        print(angle_master)

        percent16 = np.percentile(angle_master, 15.9, axis=0)
        median50  = np.percentile(angle_master, 50,   axis=0)
        percent84 = np.percentile(angle_master, 84.1, axis=0)
        print(percent16, median50, percent84, sep='\n')

        ax.plot(z_master, percent16, color='red', lw=1)
        ax.plot(z_master, median50, color='red', lw=2.5, marker='o')
        ax.plot(z_master, percent84, color='red', lw=1)

        items_labels = r"""$(\mathbf{{\widehat{{L,v_{{pec}}}}}})$ REDSHIFT TRENDS
                            Simulations: {:s}
                            Number of clusters: {:d}
                            $z$ = {:.2f} - {:.2f}
                            Aperture radius = {:.2f} $R_{{500\ true}}$""".format(sim.simulation,
                                                                   sim.totalClusters,
                                                                   redshift_str2num(sim.redshiftAllowed[0]),
                                                                   redshift_str2num(sim.redshiftAllowed[-1]),
                                                                   aperture_float)

        print(items_labels)
        ax.text(0.03, 0.97, items_labels,
                  horizontalalignment='left',
                  verticalalignment='top',
                  transform=ax.transAxes,
                  size=15)

        ax.set_xlabel(r"$z$")
        ax.set_ylabel(r"$\Delta \theta$ \quad [degrees]")

        if not os.path.exists(os.path.join(sim.pathSave, sim.simulation_name, 'rotvel_correlation')):
            os.makedirs(os.path.join(sim.pathSave, sim.simulation_name, 'rotvel_correlation'))

        plt.savefig(os.path.join(sim.pathSave, sim.simulation_name, 'rotvel_correlation',
                                 f'redshift_rotTvelT_aperture_{aperture_id}.png'), dpi=300)







if __name__ == '__main__':
    exec(open(os.path.abspath(os.path.join(
        os.path.dirname(__file__), os.path.pardir, 'visualisation', 'light_mode.py'))).read())

    def test():
        cluster = Cluster(simulation_name = 'celr_e', clusterID = 0, redshift = 'z000p000')
        matrix = CorrelationMatrix(cluster)
        data = matrix.get_data()
        aperture = matrix.get_apertures()

        matrix.plot_matrix(data[15], aperture[15])

    def all_clusters(apertureidx):
        simulation = Simulation(simulation_name='celr_e')
        matrix_list = []
        aperture_list = []
        aperture_self_similar = []
        for id in simulation.clusterIDAllowed:
            cluster = Cluster(simulation_name='celr_e', clusterID=id, redshift='z000p101')
            print(f'Analysing cluster {cluster.clusterID}')
            matrix = CorrelationMatrix(cluster)
            data = matrix.get_data()[apertureidx]
            aperture = matrix.get_apertures()[apertureidx]
            matrix_list.append(data)
            aperture_list.append(aperture)
            aperture_self_similar.append(aperture/cluster.r500)

        if not os.path.exists(os.path.join(simulation.pathSave, simulation.simulation_name, 'rotvel_correlation')):
            os.makedirs(os.path.join(simulation.pathSave, simulation.simulation_name, 'rotvel_correlation'))

        average_aperture = np.mean(aperture_self_similar, axis=0)

        matrix.plot_matrix(matrix_list, average_aperture)
        print(f"Saving matrix | aperture {apertureidx} | redshift {cluster.redshift}")
        plt.savefig(os.path.join(simulation.pathSave, simulation.simulation_name, 'rotvel_correlation',
                                 f'meanPMstd_{cluster.redshift}_aperture_{apertureidx}.png'))



    trendz = TrendZ()
    trendz.plot_z_trends(simulation_name='celr_e', aperture_id=10)




