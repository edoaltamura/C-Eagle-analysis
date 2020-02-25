from __future__ import print_function, division, absolute_import
import numpy as np
import os

import _cluster_retriever
import _cluster_profiler
from _cluster_retriever import redshift_str2num, redshift_num2str


#################################
#                               #
#	   S I M U L A T I O N      #
# 			C L A S S           #
#							    #
#################################

class Simulation():

    def __init__(self, simulation_name = 'celr_b'):

        self.simulation_name = simulation_name
        self.pathSave = '/cosma6/data/dp004/dc-alta2/C-Eagle-analysis-work'
        self.particle_type_conversion = {        'gas': '0',
                                         'dark_matter': '1',
                                               'stars': '4',
                                         'black_holes': '5'}

        if self.simulation_name == 'ceagle':
            self.simulation = 'C-EAGLE'
            self.computer = 'cosma.dur.ac.uk'
            self.pathData = '/cosma5/data/dp004/C-EAGLE/Complete_Sample'
            self.cluster_prefix = 'CE_'
            self.totalClusters = 30
            self.clusterIDAllowed = np.linspace(0, self.totalClusters - 1, self.totalClusters, dtype=np.int)
            self.subjectsAllowed = ['particledata', 'groups', 'snapshot', 'snipshot', 'hsmldir', 'groups_snip']
            self.zcat = {
                'z_value':
                    ['z001p017', 'z000p899', 'z000p795', 'z000p703', 'z000p619', 'z000p543', 'z000p474', 'z000p411',
                     'z000p366', 'z000p352', 'z000p297', 'z000p247', 'z000p199', 'z000p155', 'z000p113', 'z000p101',
                     'z000p073', 'z000p036', 'z000p000'],
                'z_IDNumber':
                    ['011', '012', '013', '014', '015', '016', '017', '018', '019', '020', '021', '022', '023', '024',
                     '025', '026', '027', '028', '029']}
            self.redshiftAllowed = self.zcat['z_value']
            self.centralFOF_groupNumber = 1

        elif self.simulation_name == 'celr_b':
            self.simulation = 'CELR-bahamas'
            self.computer = 'cosma.dur.ac.uk'
            self.pathData = '/cosma5/data/dp004/dc-pear3/data/bahamas'
            self.cluster_prefix = 'halo_'
            self.totalClusters = 45
            self.clusterIDAllowed = np.linspace(0, self.totalClusters - 1, self.totalClusters, dtype=np.int)
            self.subjectsAllowed = ['particledata', 'groups', 'snapshot', 'snipshot', 'hsmldir', 'groups_snip']
            self.zcat = {
                'z_value':
                    ['z001p017', 'z000p899', 'z000p795', 'z000p703', 'z000p619', 'z000p543', 'z000p474', 'z000p411',
                     'z000p366', 'z000p352', 'z000p297', 'z000p247', 'z000p199', 'z000p155', 'z000p113', 'z000p101',
                     'z000p073', 'z000p036', 'z000p000'],
                'z_IDNumber':
                    ['011', '012', '013', '014', '015', '016', '017', '018', '019', '020', '021', '022', '023', '024',
                     '025', '026', '027', '028', '029']}
            self.redshiftAllowed = self.zcat['z_value']
            self.centralFOF_groupNumber = 1

        elif self.simulation_name == 'celr_e':
            self.simulation = 'CELR-eagle'
            self.computer = 'cosma.dur.ac.uk'
            self.pathData = '/cosma5/data/dp004/dc-pear3/data/eagle'
            self.cluster_prefix = 'halo_'
            self.totalClusters = 45
            self.clusterIDAllowed = np.linspace(0, self.totalClusters - 1, self.totalClusters, dtype=np.int)
            self.subjectsAllowed = ['particledata', 'groups', 'snapshot', 'snipshot', 'hsmldir', 'groups_snip']
            self.zcat = {
                'z_value':
                    ['z001p017', 'z000p899', 'z000p795', 'z000p703', 'z000p619', 'z000p543', 'z000p474', 'z000p411',
                     'z000p366', 'z000p352', 'z000p297', 'z000p247', 'z000p199', 'z000p155', 'z000p113', 'z000p101',
                     'z000p073', 'z000p036', 'z000p000'],
                'z_IDNumber':
                    ['011', '012', '013', '014', '015', '016', '017', '018', '019', '020', '021', '022', '023', '024',
                     '025', '026', '027', '028', '029']}
            self.redshiftAllowed = self.zcat['z_value']
            self.centralFOF_groupNumber = 1

        elif self.simulation_name == 'macsis':
            self.simulation = 'MACSIS'
            self.computer = 'cosma.dur.ac.uk'
            self.pathData = '/cosma5/data/dp004/dc-hens1/macsis/macsis_gas'
            self.cluster_prefix = 'halo_'
            self.totalClusters = 390
            self.clusterIDAllowed = np.linspace(0, self.totalClusters - 1, self.totalClusters, dtype=np.int)
            self.subjectsAllowed = ['particledata', 'groups', 'snapshot', 'snipshot', 'hsmldir', 'groups_snip']
            self.zcat = {
                'z_float':
                    [49.0, 19.0, 4.68754, 4.06058, 3.5304, 3.07779, 2.68795, 2.34947, 2.05331, 1.79232, 1.56074,
                     1.35389, 1.16792, 0.999664, 0.84648, 0.706144, 0.576777, 0.456775, 0.344769, 0.239577, 0.140172,
                     0.0456642, 2.22045e-16],
                'z_value':
                    ['z049p000', 'z019p000', 'z004p688', 'z004p061', 'z003p053', 'z003p078', 'z002p688', 'z002p349',
                     'z002p053', 'z001p792', 'z001p561', 'z001p354', 'z001p168', 'z001p000', 'z000p846', 'z000p706',
                     'z000p577', 'z000p457', 'z000p345', 'z000p024', 'z000p014', 'z000p046', 'z000p000'],
                'z_IDNumber':
                    ['000', '001', '002', '003', '004', '005', '006', '007', '008', '009', '010', '011', '012', '013',
                     '014', '015', '016', '017', '018', '019', '020', '021', '022']}
            self.redshiftAllowed = self.zcat['z_value']
            self.centralFOF_groupNumber = 1

            self.halo_num_catalogue_contiguous = [
                '0000', '0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009', '0010', '0011',
                '0012', '0013', '0014', '0015', '0016', '0017', '0018', '0019', '0020', '0021', '0022', '0023',
                '0024', '0025', '0026', '0027', '0028', '0029', '0030', '0031', '0032', '0033', '0034', '0035',
                '0036', '0037', '0038', '0039', '0040', '0041', '0042', '0043', '0044', '0045', '0046', '0047',
                '0048', '0049', '0050', '0051', '0052', '0053', '0054', '0055', '0056', '0057', '0058', '0059',
                '0060', '0061', '0062', '0063', '0064', '0065', '0066', '0067', '0068', '0069', '0070', '0071',
                '0072', '0073', '0074', '0075', '0076', '0077', '0078', '0079', '0080', '0081', '0082', '0083',
                '0084', '0085', '0086', '0087', '0088', '0089', '0091', '0093', '0095', '0097', '0099', '0101',
                '0103', '0105', '0107', '0108', '0111', '0113', '0115', '0118', '0120', '0122', '0125', '0127',
                '0129', '0131', '0134', '0137', '0140', '0142', '0145', '0148', '0150', '0153', '0156', '0158',
                '0161', '0163', '0166', '0168', '0170', '0173', '0175', '0178', '0180', '0182', '0186', '0189',
                '0193', '0196', '0200', '0203', '0207', '0210', '0214', '0217', '0222', '0227', '0231', '0236',
                '0240', '0245', '0250', '0254', '0259', '0263', '0270', '0277', '0284', '0291', '0298', '0305',
                '0312', '0319', '0326', '0332', '0339', '0345', '0351', '0358', '0364', '0370', '0377', '0383',
                '0389', '0395', '0403', '0411', '0419', '0427', '0435', '0443', '0451', '0459', '0467', '0475',
                '0485', '0495', '0505', '0515', '0525', '0535', '0545', '0555', '0565', '0574', '0586', '0597',
                '0608', '0619', '0630', '0641', '0652', '0663', '0674', '0685', '0698', '0711', '0724', '0736',
                '0749', '0762', '0774', '0787', '0800', '0812', '0826', '0840', '0853', '0867', '0880', '0894',
                '0908', '0921', '0935', '0948', '0963', '0977', '0991', '1005', '1019', '1034', '1048', '1062',
                '1076', '1090', '1108', '1126', '1144', '1162', '1180', '1198', '1216', '1234', '1252', '1270',
                '1291', '1312', '1333', '1353', '1374', '1395', '1415', '1436', '1457', '1477', '1500', '1523',
                '1546', '1569', '1592', '1615', '1638', '1661', '1684', '1707', '1736', '1765', '1794', '1823',
                '1852', '1881', '1910', '1939', '1968', '1997', '2030', '2062', '2095', '2127', '2159', '2192',
                '2224', '2257', '2289', '2321', '2356', '2391', '2426', '2461', '2495', '2530', '2565', '2600',
                '2635', '2669', '2709', '2749', '2789', '2829', '2869', '2909', '2949', '2989', '3029', '3068',
                '3114', '3160', '3206', '3252', '3298', '3344', '3390', '3436', '3482', '3528', '3576', '3623',
                '3670', '3717', '3764', '3811', '3858', '3905', '3952', '3999', '4055', '4110', '4166', '4221',
                '4277', '4332', '4388', '4443', '4499', '4554', '4619', '4684', '4749', '4813', '4878', '4943',
                '5007', '5072', '5137', '5201', '5277', '5352', '5427', '5503', '5578', '5653', '5729', '5804',
                '5879', '5954', '6035', '6116', '6197', '6278', '6358', '6439', '6520', '6601', '6682', '6762',
                '6851', '6940', '7029', '7118', '7207', '7296', '7385', '7474', '7563', '7652', '7752', '7852',
                '7952', '8052', '8152', '8252', '8352', '8452', '8552', '8652', '8763', '8873', '8983', '9093',
                '9203', '9313', '9423', '9533', '9643', '9753']

        elif self.simulation_name == 'bahamas':
            self.simulation = 'BAHAMAS'
            self.computer = 'virgo_nas@mizar.jb.man.ac.uk'
            self.pathData = ''
            self.cluster_prefix = 'halo_'
            self.totalClusters = 45
            self.clusterIDAllowed = np.linspace(0, self.totalClusters - 1, self.totalClusters, dtype=np.int)
            self.subjectsAllowed = ['particledata', 'groups', 'snapshot', 'snipshot', 'hsmldir', 'groups_snip']
            self.zcat = {
                'z_value':
                    ['z001p017', 'z000p899', 'z000p795', 'z000p703', 'z000p619', 'z000p543', 'z000p474', 'z000p411',
                     'z000p366', 'z000p352', 'z000p297', 'z000p247', 'z000p199', 'z000p155', 'z000p113', 'z000p101',
                     'z000p073', 'z000p036', 'z000p000'],
                'z_IDNumber':
                    ['011', '012', '013', '014', '015', '016', '017', '018', '019', '020', '021', '022', '023', '024',
                     '025', '026', '027', '028', '029']}
            self.redshiftAllowed = self.zcat['z_value']
            self.centralFOF_groupNumber = 1

        else:
            raise(ValueError("Simulation name error: expected [`ceagle` or, `celr_b` or, `celr_e` or, `macsis` "
                             "or, `bahamas`], got {}.".format(simulation_name)))



    def set_pathData(self, newPath: str):
        self.pathData = newPath

    def set_totalClusters(self, newNumber: int):
        self.totalClusters = newNumber

    def get_redshiftAllowed(self, dtype=float):
        """	Access the allowed redshifts in the simulation.	"""
        if dtype == str:
            return self.redshiftAllowed
        if dtype == float:
            return [redshift_str2num(z) for z in self.redshiftAllowed]

    def info(self):
        for attr in dir(self):
            print("obj.%s = %r" % (attr, getattr(self, attr)))

    def halo_Num(self, n: int):
        """
        Returns the halo number in format e.g. 00, 01, 02
        """
        if self.simulation_name == 'macsis':
            return self.halo_num_catalogue_contiguous[n]
        else:
            if self.totalClusters > 1 and self.totalClusters < 10:
                return '%01d' % (n,)
            elif self.totalClusters > 10 and self.totalClusters < 100:
                return '%02d' % (n,)
            elif self.totalClusters > 100 and self.totalClusters < 1000:
                return '%03d' % (n,)
            elif self.totalClusters > 1000 and self.totalClusters < 10000:
                return '%04d' % (n,)


#################################
#                               #
#		  C L U S T E R  	    #
# 			C L A S S           #
#							    #
#################################

class Cluster(Simulation,
              _cluster_retriever.Mixin,
              _cluster_profiler.Mixin):

    def __init__(self,
                 simulation_name: str = None,
                 clusterID: int = 0,
                 redshift: str = 0.0,
                 comovingframe: bool = False,
                 requires: dict = {}
                 ):

        # Link to the base class by initialising it
        super().__init__(simulation_name = simulation_name)

        # Initialise and validate attributes
        self.set_simulation_name(simulation_name)
        self.set_clusterID(clusterID)
        self.set_redshift(redshift)
        self.comovingframe = comovingframe
        self.requires = requires
        self.import_requires()

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

    def path_from_cluster_name(self):
        """
        RETURNS: string type. Path of the hdf5 file to extract data from.
        """
        # os.chdir(sys.path[0])	# Set working directory as the directory of this file.
        master_directory = self.pathData
        cluster_ID = self.cluster_prefix + self.halo_Num(self.clusterID)
        data_dir = 'data'
        return os.path.join(master_directory, cluster_ID, data_dir)

    # Set additional attributes from methods
    # self.hubble_param = self.file_hubble_param()
    # self.comic_time = self.file_comic_time()
    # self.redshift = self.file_redshift()
    # self.OmegaBaryon = self.file_OmegaBaryon()
    # self.Omega0 = self.file_Omega0()
    # self.OmegaLambda = self.file_OmegaLambda()

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
                if field == 'masses':
                    setattr(self, part_type+'_'+field, self.particle_masses(part_type[-1]))
                elif field == 'coordinates':
                    setattr(self, part_type+'_'+field, self.particle_coordinates(part_type[-1]))
                elif field == 'velocity':
                    setattr(self, part_type+'_'+field, self.particle_velocity(part_type[-1]))
                elif field == 'temperature':
                    setattr(self, part_type+'_'+field, self.particle_temperature(part_type[-1]))
                elif field == 'sphdensity':
                    setattr(self, part_type+'_'+field, self.particle_SPH_density(part_type[-1]))
                elif field == 'sphkernel':
                    setattr(self, part_type+'_'+field, self.particle_SPH_smoothinglength(part_type[-1]))
                elif field == 'metallicity':
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
