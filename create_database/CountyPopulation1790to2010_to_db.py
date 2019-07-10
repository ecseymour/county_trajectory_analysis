import os
import csv
import sqlite3 as sql

topdir = os.path.abspath("__file__" + "/../../") # get parent path

db = topdir+"/output/db.sqlite"
con = sql.connect(db)
cur = con.cursor()
infile = topdir+"/data/CountyPopulation1790to2010.csv"

# create table schema
with open(infile, "rb") as f:
	field_only = []
	schema = []
	reader = csv.reader(f)
	header = reader.next()
	for i, x in enumerate(header):
		field_name = x.upper()
		field_name = field_name.replace('.', '').replace('-','')
		dtype = None
		if i <= 3:
			dtype = 'TEXT'
		else:
			dtype = 'REAL'
		field_only.append(field_name)
		field = (field_name, dtype)
		field = ' '.join(field)
		schema.append(field)

# drop table if exists
cur.execute("DROP TABLE IF EXISTS county_population;")
# create table using custom schema
cur.execute("CREATE TABLE IF NOT EXISTS county_population ({});".format( ', '.join(map(str, schema))))

# create insert template
cur.execute("SELECT * FROM county_population;")
fields = list([cn[0] for cn in cur.description])
qmarks = ["?"] * len(fields)
insert_tmpl = "INSERT INTO county_population ({}) VALUES ({});".format(', '.join(map(str, fields)),', '.join(map(str, qmarks)))

# process census 2010 data
with open(infile, 'rb') as f:
	reader = csv.reader(f)
	header = reader.next()
	for row in reader:
		cur.execute(insert_tmpl, row)

con.commit()
print "rows added: {}".format(con.total_changes)

# create index on gisjoin field
cur.execute("CREATE INDEX idx_countypopulation_gisjoin ON county_population(GISJOIN);")
cur.execute("CREATE INDEX idx_countypopulation_geoid10 ON county_population(GEOID10);")

con.close()