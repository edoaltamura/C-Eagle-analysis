from clusters_retriever import *
from cluster_profiler import *

ceagle = Simulation()
z_catalogue = ceagle.get_redshiftAllowed(dtype = float)
cluster = Cluster(clusterID = 0, redshift = z_catalogue[-1])
print(cluster.group_centre_of_potential())
