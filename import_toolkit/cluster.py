from __future__ import print_function, division, absolute_import
from typing import List, Dict, Tuple
import os
import numpy as np

from .simulation import Simulation
from . import _cluster_retriever
from . import _cluster_profiler

class Cluster(Simulation,
              _cluster_retriever.Mixin,
              _cluster_profiler.Mixin):

    def __init__(self,
                 simulation_name: str = None,
                 clusterID: int = 0,
                 redshift: str = None,
                 comovingframe: bool = False,
                 requires: Dict[str, List[str]] = None):

        # Link to the base class by initialising it
        super().__init__(simulation_name = simulation_name)

        # Initialise and validate attributes
        self.set_simulation_name(simulation_name)
        self.set_clusterID(clusterID)
        self.set_redshift(redshift)
        self.comovingframe = comovingframe
        self.requires = requires
        self.import_requires()

        # Set additional cosmoloy attributes from methods
        self.hubble_param = self.file_hubble_param()
        self.comic_time   = self.file_comic_time()
        self.z            = self.file_redshift()
        self.OmegaBaryon  = self.file_OmegaBaryon()
        self.Omega0       = self.file_Omega0()
        self.OmegaLambda  = self.file_OmegaLambda()

        # Set FoF attributes
        self.centre_of_potential = self.group_centre_of_potential()
        self.r200  = self.group_r200()
        self.r500  = self.group_r500()
        self.r2500 = self.group_r2500()
        self.Mtot  = self.group_mass()
        self.M200  = self.group_M200()
        self.M500  = self.group_M500()
        self.M2500 = self.group_M2500()
        self.NumOfSubhalos = self.NumOfSubhalos(central_FOF = self.centralFOF_groupNumber)

    def set_simulation_name(self, simulation_name: str) -> None:
        """
        Function to set the simulation_name attribute and assign it to the Cluster object.

        :param simulation_name: expect str
            The name of the simulation to retrieve the cluster from.

        :return: None type
        """
        assert (simulation_name in ['ceagle', 'celr_b', 'celr_e', 'macsis', 'bahamas']), \
            "`simulation_name` not recognised."
        self.simulation_name = simulation_name

    def set_clusterID(self, clusterID: int) -> None:
        """
        Function to set the cluster_ID attribute and assign it to the Cluster object.

        :param clusterID: expect int
            The number_ID of the cluster to be assigned to the Cluster object.

        :return: None type
        """
        assert (clusterID in self.clusterIDAllowed), 'clusterID out of bounds.'
        self.clusterID = clusterID

    def set_redshift(self, redshift: str) -> None:
        """
        Function to set the redshift_string attribute and assign it to the Cluster object.

        :param redshift: expect str
            The redshift in string form (EAGLE convention).

        :return: None type
        """
        assert (redshift in self.redshiftAllowed), "`redshift` value not recognised."
        self.redshift = redshift

    def set_requires(self, imports: dict) -> None:
        self.requires = imports
        if self.requires == None:
            print('[ SetRequires ]\t==> Warning: no pull requests for cluster datasets.')


    def path_from_cluster_name(self):
        """
        RETURNS: string type. Path of the hdf5 file to extract data from.
        """
        # os.chdir(sys.path[0])	# Set working directory as the directory of this file.
        master_directory = self.pathData
        cluster_ID = self.cluster_prefix + self.halo_Num(self.clusterID)
        data_dir = 'data'
        return os.path.join(master_directory, cluster_ID, data_dir)


    def file_hubble_param(self):
        _, attr_value = self.extract_header_attribute_name('HubbleParam')
        return attr_value

    def file_comic_time(self):
        _, attr_value = self.extract_header_attribute_name('Time')
        return attr_value

    def file_redshift(self):
        _, attr_value = self.extract_header_attribute_name('Redshift')
        return attr_value

    def file_OmegaBaryon(self):
        _, attr_value = self.extract_header_attribute_name('OmegaBaryon')
        return attr_value

    def file_Omega0(self):
        _, attr_value = self.extract_header_attribute_name('Omega0')
        return attr_value

    def file_OmegaLambda(self):
        _, attr_value = self.extract_header_attribute_name('OmegaLambda')
        return attr_value

    def file_Ngroups(self):
        _, attr_value = self.extract_header_attribute_name('TotNgroups')
        return attr_value

    def file_Nsubgroups(self):
        _, attr_value = self.extract_header_attribute_name('TotNsubgroups')
        return attr_value

    def file_MassTable(self):
        _, attr_value = self.extract_header_attribute_name('MassTable')
        return attr_value

    def file_NumPart_Total(self):
        """
        [
            NumPart_Total(part_type0),
            NumPart_Total(part_type1),
            NumPart_Total(part_type2),
            NumPart_Total(part_type3),
            NumPart_Total(part_type4),
            NumPart_Total(part_type5)
        ]

        :return: array of 6 elements
        """
        _, attr_value = self.extract_header_attribute_name('NumPart_Total')
        return attr_value

    def DM_particleMass(self):
        return self.file_MassTable()[1]

    def DM_NumPart_Total(self):
        return self.file_NumPart_Total()[1]

    def import_requires(self):
        """
        -------------------------------------------------------------------------
        Mask method to select only the particles used in the
        analysis, excluding all those which would be thrown out at some
        point of the pipeline.
        An example of these are the unbound particles with group_number < 0.
        The equation of state and particles beyond the high-resolution zoom
        regions are other examples of particles which would not be used in
        the pipeline.
        By cutting out the unwanted particles at runtime, the pipeline is
        left with fewer particles to store in the RAM memory, preventing
        overflow errors and allowing to use a lower number of cores to achieve
        similar speedups.

        No arguments are specified in this method. The input is the self.requirenments
        attribute, which specifies what datasets to import.

        [FUNCTIONALITY]
        Loop over each particle type at a time and for each do:
            - Check all particles with groupnumber > 0 (bound particles)
            - OPTIONAL: only retain groupnumber == 1 (Central FOF)
            - Import all fields required, filtering by groupnumber already
            - Filter the particle data by EoS and clean radius
            - Over write the particle field with the filtered dataset

        If the dataset belongs to the gas particle type, filter out the equation
        of state.

        [TODO]
        Implement specific equation of states for each simulation, since they all
        use different models.
        Implement booleans for switching the filtering conditions on and off.

        :return: None
            Assigns new datasets to the cluster objects. These can be easily and
            quickly accessed from the RAM.
        -------------------------------------------------------------------------
        """
        for part_type in self.requires.keys():

            group_number_index = np.where(self.group_number_part(part_type[-1]) == 1)[0]

            for field in self.requires[part_type]:

                if field == 'mass' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_masses(part_type[-1])[group_number_index])

                elif field == 'coordinates' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_coordinates(part_type[-1])[group_number_index])

                elif field == 'velocity' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_velocity(part_type[-1])[group_number_index])

                elif field == 'temperature' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_temperature(part_type[-1])[group_number_index])

                elif field == 'sphdensity' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_SPH_density(part_type[-1])[group_number_index])

                elif field == 'sphkernel' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_SPH_smoothinglength(part_type[-1])[group_number_index])

                elif field == 'metallicity' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_metallicity(part_type[-1])[group_number_index])


            radial_dist = np.linalg.norm(
                np.subtract(getattr(self, part_type+'_coordinates'), self.centre_of_potential), axis=1
            )

            clean_radius_index = np.where(radial_dist < 5*self.r200)[0]

            if (part_type == 'partType0' and
                hasattr(self, 'partType0_sphdensity') and
                hasattr(self, 'partType0_temperature')):

                log_temperature_cut = np.log10(
                    self.density_units(self.partType0_sphdensity, unit_system='nHcgs')) / 3 + 4.7

                equation_of_state_index = np.where(
                    (self.partType0_temperature > 1e4) &
                    (np.log10(self.partType0_temperature) > log_temperature_cut)
                )[0]

                intersected_index = np.intersect1d(clean_radius_index, equation_of_state_index)

            else:
                intersected_index = clean_radius_index

            print(self.simulation_name, part_type, sep='\n')
            a = len(self.group_number_part(part_type[-1]))
            b = len(intersected_index)
            print(a, b, b/a, sep='\n')

            for field in self.requires[part_type]:
                filtered_attribute = getattr(self, part_type + '_' + field)[intersected_index]
                setattr(self, part_type + '_' + field, filtered_attribute)





if __name__ == '__main__':

    import inspect

    class TEST:
        data_required = {'partType0': ['mass', 'coordinates', 'velocity', 'temperature', 'sphdensity'],
                         'partType1': ['mass', 'coordinates', 'velocity'],
                         'partType4': ['mass', 'coordinates', 'velocity']}

        def cluster_imports(self):
            print(inspect.stack()[0][3])
            cluster = Cluster(simulation_name='ceagle',
                              clusterID=0,
                              redshift='z000p000',
                              comovingframe=False,
                              requires=self.data_required)

            cluster.import_requires()

            # cluster.info()

    test = TEST()
    test.cluster_imports()
