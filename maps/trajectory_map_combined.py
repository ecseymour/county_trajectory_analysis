'''
USE FOR SCRATCH VIZ OF DIFF CLUSTER SOLUTIONS
DO NOT HARD CODE CUSTOM LABEL NAMES
'''
import os
from pysqlite2 import dbapi2 as sql
import geopandas as gpd
# from custom_geopandas_plotting import plot_dataframe_custom
from geopandas_plotting_newest_labs import plot_dataframe_newest
import pandas as pd
import csv
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import brewer2mpl


# print brewer2mpl.print_maps('qualitative', 8)
bmap = brewer2mpl.get_map('Dark2', 'Qualitative', 8)

for i, x in enumerate(bmap.mpl_colors):
	print i, x

cmap_loss = mpl.colors.ListedColormap(bmap.mpl_colors[:4], 'cmap_loss')
cmap_growth = mpl.colors.ListedColormap(bmap.mpl_colors[4:], 'cmap_growth')
cmap_combo = mpl.colors.ListedColormap(bmap.mpl_colors, 'cmap_combo')

topdir = os.path.abspath("__file__" + "/../../") # get parent path

plt.style.use(topdir+'/scripts/maps/custom.mplstyle')
db = topdir+"/output/db.sqlite"

con = sql.connect(db)
con.enable_load_extension(True)
con.execute("SELECT load_extension('mod_spatialite');")
cur = con.cursor()

############################################################################
############################################################################
############################################################################
############################################################################
############################################################################
fig = plt.figure()
ax = fig.add_subplot(111)

############################################################################
############################################################################
# BOTH	
############################################################################
############################################################################
# loss data
inF = topdir+"/output/TraMineR_loss_omspell.csv"
df = pd.read_csv(inF, usecols=[0,7], dtype={'Unnamed: 0': str})
df.columns = ['geoid10', 'cluster']

qry = '''
SELECT geo_id, state || county AS geoid10, Hex(ST_AsBinary(geometry)) AS geom
FROM gz_2010_us_050_00_20m
WHERE state NOT IN ('02', '15', '72')
-- WHERE state IN ('26')
;
'''
df_bkgrd = gpd.GeoDataFrame.from_postgis(qry, con, geom_col='geom')
df_clust = df_bkgrd.merge(df, on='geoid10')
############################################################################
# growth data
inF = topdir+"/output/TraMineR_growth_omspell.csv"
df = pd.read_csv(inF, usecols=[0,7], dtype={'Unnamed: 0': str})
df.columns = ['geoid10', 'cluster']

qry = '''
SELECT geo_id, state || county AS geoid10, Hex(ST_AsBinary(geometry)) AS geom
FROM gz_2010_us_050_00_20m
WHERE state NOT IN ('02', '15', '72')
-- WHERE state IN ('26')
;
'''
df_bkgrd = gpd.GeoDataFrame.from_postgis(qry, con, geom_col='geom')
df2 = df_bkgrd.merge(df, on='geoid10')

df2.loc[df2['cluster']=='Cluster 1', 'cluster'] = 'Cluster 6'
df2.loc[df2['cluster']=='Cluster 2', 'cluster'] = 'Cluster 7'
df2.loc[df2['cluster']=='Cluster 3', 'cluster'] = 'Cluster 8'
df2.loc[df2['cluster']=='Cluster 4', 'cluster'] = 'Cluster 9'
df2.loc[df2['cluster']=='Cluster 5', 'cluster'] = 'Cluster 10'

df_clust = df_clust.append(df2)


mylabelsloss = ['Emerging Loss', 'Punctuated Loss', 'Persistent Loss', 'Isolated Loss']
mylabelsgrowth = ['Early Recovery', 'Constant Growth', 'Intermittent Growth', 'Interrupted Growth']
mylabelscombined = mylabelsloss + mylabelsgrowth

plot_dataframe_newest(df_clust, ax=ax, column='cluster', 
	edgecolor='white', linewidth=0.1, 
	legend=True, categorical=True, cmap=cmap_combo, cust_labels=mylabelscombined, legend_kwds={'ncol':2})
############################################################################
qry = '''
SELECT geo_id, Hex(ST_AsBinary(geometry)) AS geom
FROM gz_2010_us_040_00_20m
WHERE state NOT IN ('02', '15', '72')
;
'''
df_state = gpd.GeoDataFrame.from_postgis(qry, con, geom_col='geom')
df_state.plot(ax=ax, linewidth=.6, edgecolor='white', color="None")
############################################################################

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)
ax.set_aspect("equal")
leg = ax.get_legend()
leg.set_bbox_to_anchor((0.55, -0.15, 0.2, 0.2))
leg.get_frame().set_linewidth(0.0)


outFile = topdir+"/output/trajectory_map_combined.png"
plt.savefig(outFile, bbox_inches='tight', dpi=300)
con.close()