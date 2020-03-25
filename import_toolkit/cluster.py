from __future__ import print_function, division, absolute_import
import os
import Simulation
from import_toolkit import _cluster_retriever
from import_toolkit import _cluster_profiler

class Cluster(Simulation,
              _cluster_retriever.Mixin,
              _cluster_profiler.Mixin):

    def __init__(self,
                 simulation_name: str = None,
                 clusterID: int = 0,
                 redshift: str = None,
                 comovingframe: bool = False):

        # Link to the base class by initialising it
        super().__init__(simulation_name = simulation_name)

        # Initialise and validate attributes
        self.set_simulation_name(simulation_name)
        self.set_clusterID(clusterID)
        self.set_redshift(redshift)
        self.comovingframe = comovingframe

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
        """

        :param imports:
        :return:
        """
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
        """
        AIM: retrieves the Hubble parameter of the file
        RETURNS: type = double
        """
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
        for part_type in self.requires.keys():
            for field in self.requires[part_type]:
                if field == 'mass' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_masses(part_type[-1]))
                elif field == 'coordinates' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_coordinates(part_type[-1]))
                elif field == 'velocity' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_velocity(part_type[-1]))
                elif field == 'temperature' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_temperature(part_type[-1]))
                elif field == 'sphdensity' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_SPH_density(part_type[-1]))
                elif field == 'sphkernel' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_SPH_smoothinglength(part_type[-1]))
                elif field == 'metallicity' and not hasattr(self, part_type+'_'+field):
                    setattr(self, part_type+'_'+field, self.particle_metallicity(part_type[-1]))




if __name__ == '__main__':

    import inspect

    class TEST:
        data_required = {'partType0': ['coordinates', 'velocities', 'temperature', 'sphkernel'],
                         'partType1': ['coordinates', 'velocities']}

        def cluster_imports(self):
            print(inspect.stack()[0][3])
            cluster = Cluster(simulation_name='celr_e',
                              clusterID=0,
                              redshift='z000p000',
                              comovingframe=False,
                              requires=self.data_required)

            cluster.info()

    test = TEST()
    test.cluster_imports()