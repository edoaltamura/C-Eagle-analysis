import sys
import os.path
import numpy as np
import matplotlib.colors as colors
from matplotlib import pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.axes_grid1 import make_axes_locatable


import swiftsimio_binder as swift
from losgeometry import LosGeometry
from unyt import hydrogen_mass, speed_of_light, thompson_cross_section

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from import_toolkit.cluster import Cluster
from import_toolkit.simulation import Simulation
from testing import angular_momentum



def rescale(X, x_min, x_max):
    """
    Rescaled the array of input to the range [x_min, x_max] linearly.
    This method is often used in the context of making maps with matplotlib.pyplot.inshow.
    The matrix to be accepted must contain arrays in the [0,1] range.

    :param X: numpy.ndarray
        This is the input array to be rescaled.
    :param x_min: float or int
        The lower boundary for the array to have.
    :param x_max: float or int
        The upper boundary for the new array to have.

    :return: numpy.ndarray
        The array, linearly rescaled to the range [x_min, x_max].
    """
    nom = (X - X.min(axis=0)) * (x_max - x_min)
    denom = X.max(axis=0) - X.min(axis=0)
    return x_min + nom / denom

class KSZMAP(Simulation):

    REQUIRES = {'partType0': ['coordinates', 'velocities', 'temperature', 'sphkernel', 'mass']}

    # Inherit only some methods
    info = Simulation.__dict__["info"]

    def __init__(self,
                 cluster: Cluster,
                 resolution: int = 200,
                 aperture: float = None,
                 plotlimits: float = None):
        """

        :param cluster:
        :param resolution:
        :param aperture:
        :param plotlimits:
        """

        # Impose cluste             r requirements
        cluster.set_requires(self.REQUIRES)
        cluster.import_requires()

        # Initialise the KSZ map fields
        self.cluster = cluster
        self.resolution = resolution
        self.aperture = cluster.r500 if aperture == None else aperture
        self.plotlimits = 3*cluster.r500 if plotlimits == None else plotlimits


    def make_panel(self, axes: plt.Axes.axes) -> plt.imshow:
        """
        Returns the
        :param projection:
        :return:
        """
        # Derotate cluster
        coords, vel = angular_momentum.derotate(self.cluster,
                                                align='gas',
                                                aperture_radius=self.aperture,
                                                cluster_rest_frame=True)

        # Filter particles
        spatial_filter = np.where((np.abs(coords[:, 0]) < self.plotlimits) &
                                  (np.abs(coords[:, 1]) < self.plotlimits) &
                                  (self.cluster.partType0_temperature > 1e5))[0]

        coords     = coords[spatial_filter, :]
        vel        = vel[spatial_filter, :]
        mass       = self.cluster.partType0_mass[spatial_filter]
        SPH_kernel = self.cluster.partType0_sphkernel[spatial_filter]

        constant_factor = (-1) * thompson_cross_section / (speed_of_light * hydrogen_mass / 1.16)
        kSZ = np.multiply((vel.T * mass).T, constant_factor)

        x = np.asarray(rescale(coords[:, 0], 0, 1), dtype=np.float64)
        y = np.asarray(rescale(coords[:, 1], 0, 1), dtype=np.float64)
        z = np.asarray(rescale(coords[:, 2], 0, 1), dtype=np.float64)
        m = np.asarray(kSZ[:, 2], dtype=np.float32)
        h = np.asarray(SPH_kernel, dtype=np.float32)

        # Generate the sph-smoothed map
        temp_map = swift.generate_map(x, y, m, h, self.resolution, parallel=True)
        norm = colors.SymLogNorm(linthresh=1e-5, linscale=0.5,
                                 vmin=-np.abs(temp_map).max(),
                                 vmax= np.abs(temp_map).max())

        # Attach the image to the Axes class
        image = axes.imshow(temp_map, cmap='RdBu', norm=norm, origin='lower',
                            extent=(-self.plotlimits, self.plotlimits,
                                    -self.plotlimits, self.plotlimits))

        axes.axhline(y=0, linewidth=1., color='black', linestyle='-', alpha = 0.3)
        axes.axvline(x=0, linewidth=1., color='black', linestyle='-', alpha = 0.3)
        return image

    def draw_circle(self, axes, centre: tuple = (0,0), radius: float = None, label: str = None):

        axes.add_artist(Circle(centre, radius=radius, color='black', fill=False, linestyle='--', linewidth=1.5))
        axes.annotate(label, (centre[0], centre[1] + 1.05 * radius),
                      va="bottom", ha="center", size = 20,
                      bbox=dict(boxstyle="round", facecolor="none", edgecolor='none', alpha=1))

    def make_cluster_label(self, axes: plt.Axes.axes):
        items_labels = r"""rkSZ PROJECTION MAP
                        Cluster {:s}\ {:d}
                        $z$ = {:.3f}
                        $R_{{500\ true}}$ = {:.2f} Mpc
                        Aperture radius = {:.2f} Mpc
                        Map resolution = {:.4f} kpc""".format(cluster.simulation,
                                                              cluster.clusterID,
                                                              cluster.z,
                                                              cluster.r500,
                                                              self.aperture,
                                                              2*self.plotlimits/self.resolution * 1e3)

        print(items_labels)
        axes.text(0.03, 0.97, items_labels,
                  horizontalalignment='left',
                  verticalalignment='top',
                  transform=axes.transAxes,
                  size = 20)


    def make_plot(self):

        fig = plt.figure(figsize=(12, 12))
        ax = fig.add_subplot(111)
        # Annotate cluster map
        self.make_cluster_label(ax)
        panel = self.make_panel(ax)

        # Manipulate the colorbar on the side
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="3%", pad=0.)
        cbar = fig.colorbar(panel, cax=cax)
        cbar.ax.minorticks_off()
        cbar.ax.set_ylabel(r'$y_{rKSZ} \equiv \frac{\Delta T}{T_{CMB}}$', rotation=270, size = 25, labelpad=30)

        ax.set_xlabel(r'$x\quad \mathrm{[Mpc]}$')
        ax.set_ylabel(r'$z\quad \mathrm{[Mpc]}$')
        self.draw_circle(ax, radius = cluster.r500, label = r'$R_{500\ true}$')

        observer = LosGeometry(fig)
        observer.set_inset_geometry(0.60, 0.12, 0.25, 0.25)
        observer.set_observer(rot_x=0, rot_y=0, rot_z=0)
        vectors = [
            [0, 1, 1],
            [2, 5, 6],
            [-3, -2, 0]
        ]
        labels = [r'$\mathbf{L}_\mathrm{gas}$',
                  r'$\mathbf{L}_\mathrm{DM}$',
                  r'$\mathbf{L}_\mathrm{stars}$']
        observer.plot_angularmomentum_vectors(vectors,
                                              labels=labels,
                                              plot_unitSphere=True,
                                              normalise_length=False,
                                              make_all_unitary=True)

        observer.draw_legend(ax)



if __name__ == '__main__':
    exec(open('visualisation/light_mode.py').read())

    # Create a cluster object
    cluster = Cluster(simulation_name='ceagle', clusterID=0, redshift='z000p000')

    # Create a KSZMAP object and link it to the cluster object
    test_map = KSZMAP(cluster,
                      resolution = 300,
                      aperture = cluster.r2500,
                      plotlimits = 3*cluster.r2500 )
    test_map.info()
    # Test the map output
    test_map.make_plot()
    plt.show()