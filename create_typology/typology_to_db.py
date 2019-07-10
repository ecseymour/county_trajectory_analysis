'''
write typology results to DB.
label clusters with descriptive names
'''

import os
import sqlite3 as sql
import numpy as np
import pandas as pd

from datetime import datetime
startTime = datetime.now()

topdir = os.path.abspath("__file__" + "/../../") # get parent path

db = topdir+"/output/db.sqlite"
print db
con = sql.connect(db)
cur = con.cursor()

loss_data = topdir+"/output/TraMineR_loss_omspell.csv"
df = pd.read_csv(loss_data, dtype={'Unnamed: 0': str})
df.rename(mapper={'Unnamed: 0': 'FIPS', 'cl4.lab': 'cluster'}, axis='columns', inplace=True)
df.index = df['FIPS']
df.drop(labels=['FIPS'], axis='columns', inplace=True)
df['loss_flag'] = 'loss'
# name clusters
df.loc[df['cluster']=='Cluster 1', 'label'] = 'Emerging Loss'
df.loc[df['cluster']=='Cluster 2', 'label'] = 'Punctuated Growth'
df.loc[df['cluster']=='Cluster 3', 'label'] = 'Persistent Loss'
df.loc[df['cluster']=='Cluster 4', 'label'] = 'Isolated Loss'

# append growth data
growth_data = topdir+"/output/TraMineR_growth_omspell.csv"
df2 = pd.read_csv(growth_data, dtype={'Unnamed: 0': str})
df2.rename(mapper={'Unnamed: 0': 'FIPS', 'cl4.lab': 'cluster'}, axis='columns', inplace=True)
df2.index = df2['FIPS']
df2.drop(labels=['FIPS'], axis='columns', inplace=True)
df2['loss_flag'] = 'loss'
# name clusters
df2.loc[df2['cluster']=='Cluster 1', 'label'] = 'Early Recovery'
df2.loc[df2['cluster']=='Cluster 2', 'label'] = 'Constant Growth'
df2.loc[df2['cluster']=='Cluster 3', 'label'] = 'Intermittent Growth'
df2.loc[df2['cluster']=='Cluster 4', 'label'] = 'Interrupted Growth'

# append datasets
df = df.append(df2)

# add prefix to year variables
df = df.rename(columns={'60': '1960', '70': '1970', '80': '1980', '90': '1990', '00': '2000', '10': '2010'})

print df.head()
df.to_sql('cluster_results', con, if_exists='replace')
cur.execute("CREATE INDEX idx_clusterresults_fips ON cluster_results(FIPS);")

con.close()