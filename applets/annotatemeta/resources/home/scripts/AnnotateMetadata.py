###############################################
##SCRIPT BY  :  Ow Jack Ling, Yifei Men
##CREATED    :  14 Jun 2016
##INPUT      :
##DESCRIPTION :
##ASSUMPTION :
##D_VERSION    :  0.0.2
##P_VERSION: 1.0.0
##############################################

import csv
import sqlite3
import sys
import getopt

d1 = '\t'               # delimiter 1


"""Insert a single variant/frequency record into
the sqlite3 database"""
def insert_sqlite3(con, table_name, lead_pi, lead_pi_contact, DU_name, DU_contact, source, dataset_id, description, methodology, build, human_samples_no, controls):
    cur = con.cursor()
    sqlstring = "insert into " + table_name + " (lead_pi, lead_pi_contact,  DU_name,  DU_contact,  source,  dataset_id,  description,  methodology,  build)  values ('" + lead_pi + "','" + lead_pi_contact+"','"+ DU_name + "','" + DU_contact + "','"+ source + "','" + dataset_id + "','" + description + "','" + methodology + "','" + build + "')"
    print sqlstring
    cur.execute(sqlstring)
    

"""Initialize sqlite3 table for storing genotype
frequencies"""
def create_table(con, table_name):
    cur = con.cursor()
    sqlstring = "create table " + table_name + " (lead_pi text, lead_pi_contact text, DU_name text, DU_contact text, source text, dataset_id text, description text, methodology text, build text,  human_samples_no text, controls boolean)"
    cur.execute(sqlstring)

"""check table exist in sqlite3 db"""
def check_table(con, table_name):
    cur = con.cursor()
    sqlstring = "SELECT * FROM sqlite_master WHERE name ='" + table_name + "' and type='table'"
    cur.execute(sqlstring)

    row = cur.fetchall()

    return len(row)


"""Print error to stderr"""
def print_error(hdr, msg):
    sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))

""" Main function to annotate metadata into a DB file"""
def annotate_db(p_lead_pi, p_lead_pi_contact, p_DU_name, p_DU_contact, p_source, p_dataset_id, p_description, p_method, p_build, p_human_samples_no, p_controls):
    counter = 0
    check = False
    #indb = p_database
    indb = 'db'
    dbtable = 'cohort_metadata'

    try:
        conn = sqlite3.connect(indb)
        if check_table(conn, dbtable) == 0: 
               create_table(conn, dbtable)
        else:
               print_error("Error", "Cohort metadata already exist")

        insert_sqlite3(conn, dbtable, p_lead_pi, p_lead_pi_contact, p_DU_name, p_DU_contact, p_source, p_dataset_id, p_description, p_method, p_build, p_human_samples_no, p_controls) 

        # Commit the insert
        conn.commit()

    except sqlite3.Error as er:
        print_error("Error", "SQLite3 error: {er}".format(er=er))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'Usage: %s   <input_database>' % sys.argv[0]
        print ' e.g. %s  SummaryDB.db' % sys.argv[0]
        sys.exit()

    args = {}

    opts, extraparams = getopt.getopt(sys.argv[1:], "b:l:o:d:p:s:q:t:m:n:c:r:")
		
    for o,p in opts:
            if o == '-b':
                 args[ "build" ] = p
            elif o == '-l':
                 args[ "lead_pi" ] = p
            elif o == '-o':
                 args[ "lead_pi_contact" ] = p
            elif o == '-d':
                 args[ "DU_name" ] = p
            elif o == '-p':
                 args[ "DU_contact" ] = p
            elif o == '-s':
                 args[ "source" ] = p
            elif o == '-q':
                 args[ "dataset_id" ] = p
            elif o == '-t':
                 args[ "description" ] = p
            elif o == '-m':
                 args[ "method" ] = p
            elif o == '-n':
                 args[ "human_samples_no" ] = p
            elif o == '-c':
                 args[ "controls" ] = p
            elif o == '-r':
                 args[ "database" ] = p


    annotate_db ( args[ "lead_pi" ], args[ "lead_pi_contact" ], args[ "DU_name" ], args["DU_contact"], args["source"], args["dataset_id"], args["description"], args["method"], args[ "build" ], args["human_samples_no"],args["controls"] )
