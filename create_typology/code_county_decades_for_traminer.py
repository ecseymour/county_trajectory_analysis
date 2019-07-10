'''
prepare data for trajectory clustering.
run separate processes for loss and growth counties
based on 2000 to 2010 loss/growth outcome.
for each county and for each decadal period,
calculate self pop change and average change in neighbors,
weighted by population.
'''

import os
from pysqlite2 import dbapi2 as sql
import numpy as np
import pandas as pd
from collections import OrderedDict
# from sklearn.cluster import KMeans

from datetime import datetime
startTime = datetime.now()

topdir = os.path.abspath("__file__" + "/../../") # get parent path

db = topdir+"/output/db.sqlite"
print db
con = sql.connect(db)
cur = con.cursor()

def data_prep_loss():
	# prepare data for clustering
	con = sql.connect(db)
	con.enable_load_extension(True)
	con.execute('SELECT load_extension("mod_spatialite");')
	cur = con.cursor()
	execute = cur.execute
	fetchall = cur.fetchall

	qry = '''
	SELECT GEOID10,
	(EPOP1960 - EPOP1950) * 1.0 / EPOP1950 * 100 AS ppctchg5060,
	(EPOP1970 - EPOP1960) * 1.0 / EPOP1960 * 100 AS ppctchg6070,
	(EPOP1980 - EPOP1970) * 1.0 / EPOP1970 * 100 AS ppctchg7080,
	(EPOP1990 - EPOP1980) * 1.0 / EPOP1980 * 100 AS ppctchg8090,
	(EPOP2000 - EPOP1990) * 1.0 / EPOP1990 * 100 AS ppctchg9000,
	(POP2010 - EPOP2000) * 1.0 / EPOP2000 * 100 AS ppctchg0010
	FROM county_population
	WHERE EPOP2000 > 0
	AND STATE NOT IN ('Alaska', 'Hawaii') --exclude AK and HI--
	AND	POP2010 < EPOP2000
	;
	'''

	cur.execute(qry)
	results = fetchall()
	print "shrinking counties: {}".format(len(results))

	# create dict where key is unique combination of 2010 county fips and end yr of ten-year interval
	geoid_dict = OrderedDict()
	for row in results:
		geoid10 = row[0]
		geoid_dict[geoid10+'60'] = {'ppctchg' : row[1]}
		geoid_dict[geoid10+'70'] = {'ppctchg' : row[2]}
		geoid_dict[geoid10+'80'] = {'ppctchg' : row[3]}
		geoid_dict[geoid10+'90'] = {'ppctchg' : row[4]}
		geoid_dict[geoid10+'00'] = {'ppctchg' : row[5]}
		geoid_dict[geoid10+'10'] = {'ppctchg' : row[6]}

	year_pair_dict = {
		1 : ['1950', '1960'],
		2 : ['1960', '1970'],
		3 : ['1970', '1980'],
		4 : ['1980', '1990'],
		5 : ['1990', '2000'],
		6 : ['2000', '2010']
		}

	# find neighbors
	count=0
	for k, v in geoid_dict.iteritems():
		count+=1
		if count%100==0:
			print "count is now {}".format(count)
		geoid10 = k[:5] # extract geoid from dict key
		execute('''
			SELECT A.GEOID10, C.geoid10
			FROM county_population AS A, us_county_2010 AS C 
			JOIN us_county_2010 AS B ON A.GEOID10 = B.geoid10
			WHERE ST_Touches(B.geometry, C.geometry)
			AND C.ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name='us_county_2010' AND search_frame=B.geometry)
			AND A.geoid10 = ?
			''', ([geoid10]))
		results = fetchall()
		
		for k_yr, v_yr in year_pair_dict.iteritems():
			# collect avg pop change for nbrs through 2000
			if k_yr <= 5:
				_start = v_yr[0]
				_stop = v_yr[1]
				ppchg_lst = []
				w_list = []
				for row in results:
					nbr = row[1]
					qry = '''
						SELECT A.GEOID10, 
						(EPOP{} - EPOP{}) * 1.0 / EPOP{} * 100, EPOP{}
						FROM county_population AS A JOIN us_county_2010 AS B
						ON A.GEOID10 = B.geoid10
						WHERE A.GEOID10 = '{}';
						'''.format(_stop, _start, _start, _start, nbr)
					execute(qry)
					inner_results = fetchall()
					for inner_row in inner_results:
						ppchg_lst .append(inner_row[1])
						w_list.append(inner_row[2])
				geoid_dict[geoid10+_stop[2:]]['nbr_avg_ppctchg'] = np.average(ppchg_lst, weights=np.array(w_list))

			# collect avg pop change for nbrs 2000-2010. POP2010 does not have an 'E' before it
			elif k_yr == 6:
				_start = v_yr[0]
				_stop = v_yr[1]
				ppchg_lst = []
				w_list = []
				for row in results:
					nbr = row[1]
					qry = '''
						SELECT A.GEOID10, 
						(POP{} - EPOP{}) * 1.0 / EPOP{} * 100, EPOP{}
						FROM county_population AS A JOIN us_county_2010 AS B
						ON A.GEOID10 = B.geoid10
						WHERE A.GEOID10 = '{}';
						'''.format(_stop, _start, _start, _start, nbr)
					execute(qry)
					inner_results = fetchall()
					for inner_row in inner_results:
						ppchg_lst .append(inner_row[1])
						w_list.append(inner_row[2])
				geoid_dict[geoid10+_stop[2:]]['nbr_avg_ppctchg'] = np.average(ppchg_lst, weights=np.array(w_list))


	df = pd.DataFrame.from_dict(geoid_dict, orient='index')
	print df.head()
	print df.describe()

	outfile = topdir+'/output/vars_for_traminer_loss.pkl'
	df.to_pickle(outfile)

	con.close()


def code_periods():
	infile = topdir+'/output/vars_for_traminer_loss.pkl'
	df = pd.read_pickle(infile)
	df['category'] = None
	df.loc[ (df['ppctchg'] < 0) & (df['nbr_avg_ppctchg'] < 0), 'category'] = 'A'
	df.loc[ (df['ppctchg'] < 0) & (df['nbr_avg_ppctchg'] >= 0), 'category'] = 'B'
	df.loc[ (df['ppctchg'] >= 0) & (df['nbr_avg_ppctchg'] < 0), 'category'] = 'C'
	df.loc[ (df['ppctchg'] >= 0) & (df['nbr_avg_ppctchg'] >= 0), 'category'] = 'D'

	print df.head()

	print df[['ppctchg', 'nbr_avg_ppctchg', 'category']].groupby('category').mean()

	# reshape data so that counties are rows, years are cols and cats are vals
	df['geoid10'] = df.index.str[:5]
	df['end'] = df.index.str[5:]
	print df.head()
	
	_reshape = df.pivot(index='geoid10', columns='end', values='category')
	outfile = topdir+"/output/vars_for_traminer_loss.csv"
	_reshape = _reshape[['60', '70', '80', '90', '00', '10']]
	_reshape.to_csv(outfile)
	print _reshape.head()



def data_prep_growth():
	# prepare data for clustering
	con = sql.connect(db)
	con.enable_load_extension(True)
	con.execute('SELECT load_extension("mod_spatialite");')
	cur = con.cursor()
	execute = cur.execute
	fetchall = cur.fetchall

	qry = '''
	SELECT GEOID10,
	(EPOP1960 - EPOP1950) * 1.0 / EPOP1950 * 100 AS ppctchg5060,
	(EPOP1970 - EPOP1960) * 1.0 / EPOP1960 * 100 AS ppctchg6070,
	(EPOP1980 - EPOP1970) * 1.0 / EPOP1970 * 100 AS ppctchg7080,
	(EPOP1990 - EPOP1980) * 1.0 / EPOP1980 * 100 AS ppctchg8090,
	(EPOP2000 - EPOP1990) * 1.0 / EPOP1990 * 100 AS ppctchg9000,
	(POP2010 - EPOP2000) * 1.0 / EPOP2000 * 100 AS ppctchg0010
	FROM county_population
	WHERE EPOP2000 > 0
	AND STATE NOT IN ('Alaska', 'Hawaii') --exclude AK and HI--
	AND	POP2010 >= EPOP2000;
	'''

	cur.execute(qry)
	results = fetchall()
	print "other counties: {}".format(len(results))

	# create dict where key is unique combination of 2010 county fips and end yr of ten-year interval
	geoid_dict = OrderedDict()
	for row in results:
		geoid10 = row[0]
		geoid_dict[geoid10+'60'] = {'ppctchg' : row[1]}
		geoid_dict[geoid10+'70'] = {'ppctchg' : row[2]}
		geoid_dict[geoid10+'80'] = {'ppctchg' : row[3]}
		geoid_dict[geoid10+'90'] = {'ppctchg' : row[4]}
		geoid_dict[geoid10+'00'] = {'ppctchg' : row[5]}
		geoid_dict[geoid10+'10'] = {'ppctchg' : row[6]}

	year_pair_dict = {
		1 : ['1950', '1960'],
		2 : ['1960', '1970'],
		3 : ['1970', '1980'],
		4 : ['1980', '1990'],
		5 : ['1990', '2000'],
		6 : ['2000', '2010']
		}

	# find neighbors
	count = 0
	for k, v in geoid_dict.iteritems():
		count+=1
		geoid10 = k[:5] # extract geoid from dict key

		try:
			if geoid10 in ['25019', '25007', '53055']:
				print "now finding neighbors for {}".format(geoid10)
				execute('''
					SELECT A.GEOID10, C.geoid10
					FROM county_population AS A, tl_2010_us_county10 AS C 
					JOIN tl_2010_us_county10 AS B ON A.GEOID10 = B.geoid10
					WHERE ST_Touches(B.geometry, C.geometry)
					AND C.ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name='tl_2010_us_county10' AND search_frame=B.geometry)
					AND A.geoid10 = ?
					''', ([geoid10]))
				results = fetchall()
				
				for k_yr, v_yr in year_pair_dict.iteritems():
					# collect avg pop change for nbrs through 2000
					if k_yr <= 5:
						_start = v_yr[0]
						_stop = v_yr[1]
						ppchg_lst = []
						w_list = []
						for row in results:
							nbr = row[1]
							qry = '''
								SELECT A.GEOID10, 
								(EPOP{} - EPOP{}) * 1.0 / EPOP{} * 100, EPOP{}
								FROM county_population AS A JOIN us_county_2010 AS B
								ON A.GEOID10 = B.geoid10
								WHERE A.GEOID10 = '{}';
								'''.format(_stop, _start, _start, _start, nbr)
							execute(qry)
							inner_results = fetchall()
							for inner_row in inner_results:
								ppchg_lst .append(inner_row[1])
								w_list.append(inner_row[2])
						geoid_dict[geoid10+_stop[2:]]['nbr_avg_ppctchg'] = np.average(ppchg_lst, weights=np.array(w_list))

					# collect avg pop change for nbrs 2000-2010. POP2010 does not have an 'E' before it
					elif k_yr == 6:
						_start = v_yr[0]
						_stop = v_yr[1]
						ppchg_lst = []
						w_list = []
						for row in results:
							nbr = row[1]
							qry = '''
								SELECT A.GEOID10, 
								(POP{} - EPOP{}) * 1.0 / EPOP{} * 100, EPOP{}
								FROM county_population AS A JOIN us_county_2010 AS B
								ON A.GEOID10 = B.geoid10
								WHERE A.GEOID10 = '{}';
								'''.format(_stop, _start, _start, _start, nbr)
							execute(qry)
							inner_results = fetchall()
							for inner_row in inner_results:
								ppchg_lst .append(inner_row[1])
								w_list.append(inner_row[2])
						geoid_dict[geoid10+_stop[2:]]['nbr_avg_ppctchg'] = np.average(ppchg_lst, weights=np.array(w_list))
			else:
				if count%100==0:
					print "count is now {}".format(count)
				execute('''
					SELECT A.GEOID10, C.geoid10
					FROM county_population AS A, us_county_2010 AS C 
					JOIN us_county_2010 AS B ON A.GEOID10 = B.geoid10
					WHERE ST_Touches(B.geometry, C.geometry)
					AND C.ROWID IN (SELECT ROWID FROM SpatialIndex WHERE f_table_name='us_county_2010' AND search_frame=B.geometry)
					AND A.geoid10 = ?
					''', ([geoid10]))
				results = fetchall()
				
				for k_yr, v_yr in year_pair_dict.iteritems():
					# collect avg pop change for nbrs through 2000
					if k_yr <= 5:
						_start = v_yr[0]
						_stop = v_yr[1]
						ppchg_lst = []
						w_list = []
						for row in results:
							nbr = row[1]
							qry = '''
								SELECT A.GEOID10, 
								(EPOP{} - EPOP{}) * 1.0 / EPOP{} * 100, EPOP{}
								FROM county_population AS A JOIN us_county_2010 AS B
								ON A.GEOID10 = B.geoid10
								WHERE A.GEOID10 = '{}';
								'''.format(_stop, _start, _start, _start, nbr)
							execute(qry)
							inner_results = fetchall()
							for inner_row in inner_results:
								ppchg_lst .append(inner_row[1])
								w_list.append(inner_row[2])
						geoid_dict[geoid10+_stop[2:]]['nbr_avg_ppctchg'] = np.average(ppchg_lst, weights=np.array(w_list))

					# collect avg pop change for nbrs 2000-2010. POP2010 does not have an 'E' before it
					elif k_yr == 6:
						_start = v_yr[0]
						_stop = v_yr[1]
						ppchg_lst = []
						w_list = []
						for row in results:
							nbr = row[1]
							qry = '''
								SELECT A.GEOID10, 
								(POP{} - EPOP{}) * 1.0 / EPOP{} * 100, EPOP{}
								FROM county_population AS A JOIN us_county_2010 AS B
								ON A.GEOID10 = B.geoid10
								WHERE A.GEOID10 = '{}';
								'''.format(_stop, _start, _start, _start, nbr)
							execute(qry)
							inner_results = fetchall()
							for inner_row in inner_results:
								ppchg_lst .append(inner_row[1])
								w_list.append(inner_row[2])
						geoid_dict[geoid10+_stop[2:]]['nbr_avg_ppctchg'] = np.average(ppchg_lst, weights=np.array(w_list))
		except:
			print "+" * 100
			print "{} failed".format(geoid10)				
			print "+" * 100
	
	df = pd.DataFrame.from_dict(geoid_dict, orient='index')
	print df.head()
	print df.describe()

	outfile = topdir+'/output/vars_for_traminer_growth.pkl'
	df.to_pickle(outfile)

	con.close()


def code_periods_growth():
	infile = topdir+'/output/vars_for_traminer_growth.pkl'
	df = pd.read_pickle(infile)
	df['category'] = None
	df.loc[ (df['ppctchg'] < 0) & (df['nbr_avg_ppctchg'] < 0), 'category'] = 'A'
	df.loc[ (df['ppctchg'] < 0) & (df['nbr_avg_ppctchg'] >= 0), 'category'] = 'B'
	df.loc[ (df['ppctchg'] >= 0) & (df['nbr_avg_ppctchg'] < 0), 'category'] = 'C'
	df.loc[ (df['ppctchg'] >= 0) & (df['nbr_avg_ppctchg'] >= 0), 'category'] = 'D'

	print df.head()

	print df[['ppctchg', 'nbr_avg_ppctchg', 'category']].groupby('category').mean()

	# reshape data so that counties are rows, years are cols and cats are vals
	df['geoid10'] = df.index.str[:5]
	df['end'] = df.index.str[5:]
	print df.head()
	
	_reshape = df.pivot(index='geoid10', columns='end', values='category')
	outfile = topdir+"/output/vars_for_traminer_growth.csv"
	_reshape = _reshape[['60', '70', '80', '90', '00', '10']]
	_reshape.to_csv(outfile)
	print _reshape.head()


data_prep_loss()

code_periods()

data_prep_growth()

code_periods_growth()


print "DONE!"
print datetime.now() - startTime 
