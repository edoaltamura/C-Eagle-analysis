import numpy as np
import h5py as h5
import os
import sys

import redshift_catalogue_ceagle as zcat

#################################
#                               #
# 	G L O B    M E T H O D S    #
#							    #
#################################

def halo_Num(n: int):
	"""
	Returns the halo number in format e.g. 00, 01, 02
	"""
	return '%02d' % (n,)

def redshift_str2num(z: str):
	"""
	Converts the redshift of the snapshot from text to numerical,
	in a format compatible with the file names.
	E.g. float z = 2.16 <--- str z = 'z002p160'.
	"""
	z = z.strip('z').replace('p', '.')
	return float(z)

def redshift_num2str(z: float):
	"""
	Converts the redshift of the snapshot from numerical to
	text, in a format compatible with the file names.
	E.g. float z = 2.16 ---> str z = 'z002p160'.
	"""
	integer_z, decimal_z = divmod(z, 1)
	# Integer part
	integer_z = '%03d' % (int(integer_z),)
	# Decimal part
	decimal_z = str(int(round(decimal_z, 4)*1000)).rjust(3, '0')
	return 'z' + integer_z + 'p' + decimal_z



def free_memory(var_list, invert = False):
	"""
	Function for freeing memory dynamicallyself.
	invert allows to delete all local variables that are NOT in var_list.
	"""
	if not invert:
		for name in var_list:
			if not name.startswith('_') and name in dir():
				del globals()[name]
	if invert:
		for name in dir():
			if name in var_list and not name.startswith('_'):
				del globals()[name]




#################################
#                               #
#	   S I M U L A T I O N      #
# 			C L A S S           #
#							    #
#################################

class Simulation:

	def __init__(self):
		self.simulation = 'C-EAGLE'
		self.computer = 'cosma.dur.ac.uk'
		self.pathData = '/cosma5/data/dp004/C-EAGLE/Complete_Sample'
		self.pathSave = '/cosma6/data/dp004/dc-alta2/C-Eagle-analysis-work'
		self.totalClusters = 30
		self.clusterIDAllowed = np.linspace(0, self.totalClusters-1, self.totalClusters, dtype=np.int)
		self.subjectsAllowed = ['particledata',	'groups', 'snapshot', 'snipshot', 'hsmldir', 'groups_snip']
		self.redshiftAllowed = zcat.group_data()['z_value']

	def set_pathData(self, newPath: str):
		self.pathData = newPath

	def set_totalClusters(self, newNumber: int):
		self.totalClusters = newNumber

	def get_redshiftAllowed(self, dtype = float):
		"""	Access the allowed redshifts in the simulation.	"""
		if dtype == str:
			return self.redshiftAllowed
		if dtype == float:
			return [redshift_str2num(z) for z in self.redshiftAllowed]

#################################
#                               #
#		  C L U S T E R  	    #
# 			C L A S S           #
#							    #
#################################

class Cluster (Simulation):

	def __init__(self, *args, clusterID:int = 0, redshift:float = 0.0, subject:str = 'particledata', **kwargs):
		super().__init__()

		# Initialise and validate attributes
		self.set_clusterID(clusterID)
		self.set_redshift(redshift)
		self.set_subject(subject)

		# Pass attributed into kwargs
		kwargs['clusterID'] = self.clusterID
		kwargs['redshift'] = self.redshift
		kwargs['subject'] = self.subject

		# Set additional attributes from methods
		self.set_filePaths()
		self.hubble_param = self.file_hubble_param()
		self.comic_time = self.file_comic_time()
		self.redshift = self.file_redshift()
		# self.Ngroups = self.file_Ngroups()
		# self.Nsubgroups = self.file_Nsubgroups()
		self.OmegaBaryon = self.file_OmegaBaryon()
		self.Omega0 = self.file_Omega0()
		self.OmegaLambda = self.file_OmegaLambda()

	# Change and validate Cluster attributes
	def set_clusterID(self, clusterID: int):
		try:
			assert (type(clusterID) is int), 'clusterID must be integer.'
			assert (clusterID in self.clusterIDAllowed), 'clusterID out of bounds (00 ... 29).'
		except AssertionError:
			raise
		else:
			self.clusterID = clusterID

	def set_redshift(self, redshift: float):
		try:
			assert (type(redshift) is float), 'redshift must be float.'
			assert (redshift >= 0.0), 'Negative redshift.'
			assert (redshift_num2str(redshift) in self.redshiftAllowed), 'Redshift not valid.'
		except AssertionError:
			raise
		else:
			self.redshift = redshift

	def set_subject(self, subject: str):
		try:
			assert (subject in self.subjectsAllowed), 'Subject of data not valid.'
		except AssertionError:
			raise
		else:
			self.subject = subject

	def path_from_cluster_name(self):
		"""
		RETURNS: string type. Path of the hdf5 file to extract data from.
		"""
		#os.chdir(sys.path[0])	# Set working directory as the directory of this file.
		master_directory = 	self.pathData
		cluster_ID = 'CE_' + halo_Num(self.clusterID)
		data_dir = 'data'
		return os.path.join(master_directory, cluster_ID, data_dir)



	def file_dir_hdf5(self):
		"""	RETURNS: Name of the hdf5 directory to extract data from.	"""
		if self.subject == 'particledata':
			prefix = 'eagle_subfind_particles_'
		elif self.subject == 'groups':
			prefix = 'eagle_subfind_tab_'
		elif self.subject == 'snapshot':
			raise("[WARNING] This feature is not yet implemented in clusters_retriever.py.")
		elif self.subject == 'snipshot':
			raise("[WARNING] This feature is not yet implemented in clusters_retriever.py.")
		elif self.subject == 'hsmldir':
			raise("[WARNING] This feature is not yet implemented in clusters_retriever.py.")
		elif self.subject == 'groups_snip':
			raise("[WARNING] This feature is not yet implemented in clusters_retriever.py.")

		redshift_str = redshift_num2str(self.redshift)
		redshift_i = self.redshiftAllowed.index(redshift_str)
		redshift_index = zcat.group_data()['z_IDNumber'][redshift_i]
		sbj_string = self.subject + '_' + redshift_index + '_' + redshift_str
		file_dir = os.path.join(self.path_from_cluster_name(), sbj_string)
		file_list = os.listdir(file_dir)
		return file_dir, [x for x in file_list if x.startswith(prefix)]

	def file_CompletePath_hdf5(self):
		"""
		Function merges file directory and file names.
		Returns the complete hdf5 file paths in the form of an array of strings.
		"""
		path, h5_files = self.file_dir_hdf5()
		return sorted([os.path.join(path, file) for file in h5_files])

	def set_filePaths(self):
		""" Associate the hdf5 file paths to the object as attribute. """
		self.filePaths = self.file_CompletePath_hdf5()

	#####################################################
	#													#
	#					D A T A   						#
	# 				M A N A G E M E N T 				#
	#													#
	#####################################################

	def group_centre_of_potential(self):
		"""
		AIM: reads the FoF group central of potential from the path and file given
		RETURNS: type = np.array of 3 doubles
		ACCESS DATA: e.g. group_CoP[0] for getting the x value
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		return self.subgroups_centre_of_potential()[0]

	def group_centre_of_mass(self):
		"""
		AIM: reads the FoF group central of mass from the path and file given
		RETURNS: type = np.array of 3 doubles
		ACCESS DATA: e.g. group_CoM[0] for getting the x value
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		return self.subgroups_centre_of_mass()[0]

	def group_r200(self):
		"""
		AIM: reads the FoF virial radius from the path and file given
		RETURNS: type = double
		"""
		# Import data from hdf5 file
		h5file=h5.File(self.filePaths[0],'r')
		h5dset=h5file["/FOF/Group_R_Crit200"]
		temp=h5dset[...]
		r200c=temp[0]
		h5file.close()
		return r200c

	def group_r500(self):
		"""
		AIM: reads the FoF virial radius from the path and file given
		RETURNS: type = double
		"""
		# Import data from hdf5 file
		h5file=h5.File(self.filePaths[0],'r')
		h5dset=h5file["/FOF/Group_R_Crit500"]
		temp=h5dset[...]
		r500c=temp[0]
		h5file.close()
		return r500c

	def group_velocity(self):
		"""
		AIM: reads the group bulk motion from the path and file given
		RETURNS: type = np.array of 3 doubles
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		return self.subgroups_velocity()[0]

	def group_mass(self):
		"""
		AIM: reads the group mass from the path and file given
		RETURNS: float
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		return self.subgroups_mass()[0]

	def group_kin_energy(self):
		"""
		AIM: reads the group kin_energy from the path and file given
		RETURNS: float
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		return self.subgroups_kin_energy()[0]

	def group_therm_energy(self):
		"""
		AIM: reads the group therm_energy from the path and file given
		RETURNS: float
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		return self.subgroups_therm_energy()[0]

	def extract_header_attribute(self, element_number):
		# Import data from hdf5 file
		h5file=h5.File(self.filePaths[0],'r')
		h5dset=h5file["/Header"]
		attr_name = list(h5dset.attrs.keys())[element_number]
		attr_value = list(h5dset.attrs.values())[element_number]
		h5file.close()
		return attr_name, attr_value

	def extract_header_attribute_name(self, element_name):
		# Import data from hdf5 file
		h5file=h5.File(self.filePaths[0],'r')
		h5dset=h5file["/Header"]
		attr_name = h5dset.attrs.get(element_name, default=None)
		attr_value = h5dset.attrs.get(element_name, default=None)
		h5file.close()
		return attr_name, attr_value


	def file_hubble_param(self):
		"""
		AIM: retrieves the Hubble parameter of the file
		RETURNS: type = double
		"""
		_ , attr_value = self.extract_header_attribute_name('HubbleParam')
		return attr_value

	def file_comic_time(self):
		"""
		AIM: retrieves the Hubble parameter of the file
		RETURNS: type = double
		"""
		_ , attr_value = self.extract_header_attribute_name('Time')
		return attr_value


	def file_redshift(self):
		"""
		AIM: retrieves the redshift of the file
		RETURNS: type = double
		"""
		_ , attr_value = self.extract_header_attribute_name('Redshift')
		return attr_value


	def file_Ngroups(self):
		"""
		AIM: retrieves the redshift of the file
		RETURNS: type = double
		"""
		# Import data from multiple hdf5 files
		Ngroups = 0
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			h5dset=h5file["/Header"]
			attr_value = h5dset.attrs.get('Ngroups', default=None)
			h5file.close()
			Ngroups += attr_value
		return Ngroups


	def file_Nsubgroups(self):
		"""
		AIM: retrieves the file_Nsubgroups of the files
		RETURNS: type = double
		"""
		# Import data from multiple hdf5 files
		Nsubgroups = 0
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			h5dset=h5file["/Header"]
			attr_value = h5dset.attrs.get('Nsubgroups', default=None)
			h5file.close()
			Nsubgroups += attr_value
		return Nsubgroups


	def file_OmegaBaryon(self):
		"""
		AIM: retrieves the redshift of the file
		RETURNS: type = double
		"""
		_ , attr_value = self.extract_header_attribute_name('OmegaBaryon')
		return attr_value


	def file_Omega0(self):
		"""
		AIM: retrieves the redshift of the file
		RETURNS: type = double
		"""
		_ , attr_value = self.extract_header_attribute_name('Omega0')
		return attr_value


	def file_OmegaLambda(self):
		"""
		AIM: retrieves the redshift of the file
		RETURNS: type = double
		"""
		_ , attr_value = self.extract_header_attribute_name('OmegaLambda')
		return attr_value

	def group_numbers(self):
		"""
		AIM: retrieves the redshift of the file
		RETURNS: type = double
		"""
		# Import data from multiple hdf5 files
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		groupNumber = np.zeros(0, dtype=np.int32)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			h5dset=h5file["/Header"]
			attr_value = h5dset.attrs.get('Ngroups', default=None)
			h5file.close()
			Ngroups += attr_value
		return Ngroups

	def subgroups_centre_of_potential(self):
		"""
		AIM: reads the subgroups central of potential from the path and file given
		RETURNS: type = 2D np.array
		FORMAT:	 sub#	  x.sub_CoP 	y.sub_CoP     z.sub_CoP
					0  [[			,				,			],
					1	[			,				,			],
					2	[			,				,			],
					3	[			,				,			],
					4	[			,				,			],
					5	[			,				,			],
					.						.
					.						.
					.						.					]]

		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		pos = np.zeros( (0,3) ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/Subhalo/CentreOfPotential']
			sub_CoP = hd5set[...]
			h5file.close()
			pos = np.concatenate((pos, sub_CoP), axis = 0)
			free_memory(['pos'], invert = True)
		return pos

	def subgroups_centre_of_mass(self):
		"""
		AIM: reads the subgroups central of mass from the path and file given
		RETURNS: type = 2D np.array
		FORMAT:	 sub#	  x.sub_CoM 	y.sub_CoM     z.sub_CoM
					0  [[			,				,			],
					1	[			,				,			],
					2	[			,				,			],
					3	[			,				,			],
					4	[			,				,			],
					5	[			,				,			],
					.						.
					.						.
					.						.					]]

		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		pos = np.zeros( (0,3) ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/Subhalo/CentreOfMass']
			sub_CoM = hd5set[...]
			h5file.close()
			pos = np.concatenate((pos, sub_CoM), axis = 0)
			free_memory(['pos'], invert = True)
		return pos

	def subgroups_velocity(self):
		"""
		AIM: reads the subgroups 3d velocities from the path and file given
		RETURNS: type = 2D np.array
		FORMAT:	 sub#	    vx.sub 	 	 vy.sub       	vz.sub
					0  [[			,				,			],
					1	[			,				,			],
					2	[			,				,			],
					3	[			,				,			],
					4	[			,				,			],
					5	[			,				,			],
					.						.
					.						.
					.						.					]]

		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		vel = np.zeros( (0,3) ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/Subhalo/Velocity']
			sub_v = hd5set[...]
			h5file.close()
			vel = np.concatenate((vel, sub_v), axis = 0)
			free_memory(['vel'], invert = True)
		return vel

	def subgroups_mass(self):
		"""
		AIM: reads the subgroups masses from the path and file given
		RETURNS: type = 1D np.array
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		mass = np.zeros(0 ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/Subhalo/Mass']
			sub_m = hd5set[...]
			h5file.close()
			mass = np.concatenate((mass, sub_m))
			free_memory(['mass'], invert = True)
		return mass

	def subgroups_kin_energy(self):
		"""
		AIM: reads the subgroups kinetic energy from the path and file given
		RETURNS: type = 1D np.array
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		kin_energy = np.zeros(0 ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/Subhalo/KineticEnergy']
			sub_ke = hd5set[...]
			h5file.close()
			kin_energy = np.concatenate((kin_energy, sub_ke), axis = 0)
			free_memory(['kin_energy'], invert = True)
		return kin_energy

	def subgroups_therm_energy(self):
		"""
		AIM: reads the subgroups thermal energy from the path and file given
		RETURNS: type = 1D np.array
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		therm_energy = np.zeros(0 ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/Subhalo/ThermalEnergy']
			sub_th = hd5set[...]
			h5file.close()
			therm_energy = np.concatenate((therm_energy, sub_th), axis = 0)
			free_memory(['therm_energy'], invert = True)
		return therm_energy

	def subgroups_mass_type(self):
		"""
		AIM: reads the subgroups mass types from the path and file given
		RETURNS: type = 2D np.array
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		massType = np.zeros(0)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/Subhalo/MassType']
			sub_mType = hd5set[...]
			h5file.close()
			massType = np.concatenate((massType, sub_mType), axis = 0)
			free_memory(['massType'], invert = True)
		return massType

	def subgroups_number_of(self):
		"""
		AIM: reads the number of subgroups in FoF group from the path and file given
		RETURNS: type = 1D np.array
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		sub_N_tot = np.zeros(0 ,dtype=np.int)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['FOF/NumOfSubhalos']
			sub_N = hd5set[...]
			h5file.close()
			sub_N_tot = np.concatenate((sub_N_tot, sub_N), axis = 0)
		return sub_N_tot

	def subgroups_group_number(self):
		"""
		AIM: reads the group number of subgroups from the path and file given
		RETURNS: type = 1D np.array
		"""
		# Import data from hdf5 file
		if self.subject != 'groups':
			raise ValueError('subject of data must be groups.')
		sub_gn_tot = np.zeros(0, dtype=np.int)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['Subhalo/GroupNumber']
			sub_gn = hd5set[...]
			h5file.close()
			sub_gn_tot = np.concatenate((sub_gn_tot, sub_gn), axis = 0)
		return sub_gn_tot

	def particle_type(self, part_type = 'gas'):
		"""
		AIM: returns a string characteristic of the particle type selected
		RETURNS: string of number 0<= n <= 5
		"""
		if part_type == 'gas' or part_type == 0 or part_type == '0': return '0'
		elif part_type == 'highres_DM' or part_type == 1 or part_type == '1': return '1'
		elif part_type == 'lowres_DM' or part_type == 2 or part_type == '2': return '2'
		elif part_type == 'lowres_DM' or part_type == 3 or part_type == '3': return '3'
		elif part_type == 'stars' or part_type == 4 or part_type == '4': return '4'
		elif part_type == 'black_holes' or part_type == 5 or part_type == '5': return '5'
		else:
			print("[ERROR] You entered the wrong particle type!")
			exit(1)


	def group_number(self, part_type):
		"""
		RETURNS: np.array
		"""
		# Import data from hdf5 file
		if self.subject != 'particledata':
			raise ValueError('subject of data must be particledata.')
		group_number = np.zeros(0 ,dtype=np.int)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/PartType' + part_type + '/GroupNumber']
			sub_gn = hd5set[...]
			h5file.close()
			group_number = np.concatenate((group_number, sub_gn), axis = 0)
		return group_number


	def subgroup_number(self, part_type):
		"""
		RETURNS: np.array
		"""
		if self.subject != 'particledata':
			raise ValueError('subject of data must be particledata.')
		sub_group_number = np.zeros(0 ,dtype=np.int)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/PartType' + part_type + '/SubGroupNumber']
			sub_gn = hd5set[...]
			h5file.close()
			sub_group_number = np.concatenate((sub_group_number, sub_gn), axis = 0)
		return sub_group_number

	def particle_coordinates(self, part_type):
		"""
		RETURNS: 2D np.array
		"""
		if self.subject != 'particledata':
			raise ValueError('subject of data must be particledata.')
		pos = np.zeros( (0,3) ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/PartType' + part_type + '/Coordinates']
			sub_pos = hd5set[...]
			h5file.close()
			pos = np.concatenate((pos, sub_pos), axis = 0)
			free_memory(['pos'], invert = True)
		return pos

	def particle_velocity(self, part_type):
		"""
		RETURNS: 2D np.array
		"""
		if self.subject != 'particledata':
			raise ValueError('subject of data must be particledata.')
		part_vel = np.zeros( (0,3) ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/PartType' + part_type + '/Velocity']
			sub_vel = hd5set[...]
			h5file.close()
			part_vel = np.concatenate((part_vel, sub_vel), axis = 0)
			free_memory(['part_vel'], invert = True)
		return part_vel

	def particle_masses(self, part_type):
		"""
		RETURNS: 2D np.array
		"""
		if self.subject != 'particledata':
			raise ValueError('subject of data must be particledata.')
		if (part_type != '1'):
			part_mass = np.zeros(0 ,dtype=np.float)
			for path in self.filePaths:
				h5file=h5.File(path,'r')
				hd5set=h5file['/PartType' + part_type + '/Mass']
				sub_m = hd5set[...]
				h5file.close()
				part_mass = np.concatenate((part_mass, sub_m), axis = 0)
				free_memory(['part_mass'], invert = True)
		elif part_type == '1':
			part_mass = np.ones_like(self.group_number(part_type))*0.422664
		return part_mass


	def particle_temperature(self, part_type = '0'):
		"""
		RETURNS: 1D np.array
		"""
		if self.subject != 'particledata':
			raise ValueError('subject of data must be particledata.')
		# Check that we are extracting the temperature of gas particles
		if part_type is not '0':
			print("[ERROR] Trying to extract the temperature of non-gaseous particles.")
			exit(1)
		temperature = np.zeros(0 ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/PartType0/Temperature']
			sub_T = hd5set[...]
			h5file.close()
			temperature = np.concatenate((temperature, sub_T), axis = 0)
			free_memory(['temperature'], invert = True)
		return temperature


	def particle_SPH_density(self, part_type = '0'):
		"""
		RETURNS: 1D np.array
		"""
		if self.subject != 'particledata':
			raise ValueError('subject of data must be particledata.')
		# Check that we are extracting the temperature of gas SPH density
		if part_type is not '0':
			print("[ERROR] Trying to extract the SPH density of non-gaseous particles.")
			exit(1)
		densitySPH = np.zeros(0 ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/PartType0/Density']
			sub_den = hd5set[...]
			h5file.close()
			densitySPH = np.concatenate((densitySPH, sub_den), axis = 0)
			free_memory(['densitySPH'], invert = True)
		return densitySPH


	def particle_metallicity(self, part_type = '0'):
		"""
		RETURNS: 1D np.array
		"""
		if self.subject != 'particledata':
			raise ValueError('subject of data must be particledata.')
		# Check that we are extracting the temperature of gas SPH density
		if part_type is not '0':
			print("[ERROR] Trying to extract the metallicity of non-gaseous particles.")
			exit(1)
		metallicity = np.zeros(0 ,dtype=np.float)
		for path in self.filePaths:
			h5file=h5.File(path,'r')
			hd5set=h5file['/PartType0/Metallicity']
			sub_Z = hd5set[...]
			h5file.close()
			metallicity = np.concatenate((metallicity, sub_Z), axis = 0)
			free_memory(['metallicity'], invert = True)
		return metallicity
