###############################################
##SCRIPT BY  :  Ow Jack Ling, Yifei Men
##CREATED    :  14 Jun 2016
##INPUT      :
##DESCRIPTION :
##ASSUMPTION :
##D_VERSION    :  0.0.
##P_VERSION: 1.0.0
##############################################

import csv
import sqlite3
import sys
import vcf

d1 = '\t'               # delimiter 1
outfile = 'SummaryFile.txt'

"""Extract AF field from INFO"""
def extractAF(info):
    return info['AF'] if 'AF' in info else []

"""Write Chrom, Pos, Ref, Alt, GT to a tsv file"""
def createNewOutFile(ofile):
    with open(ofile, 'w') as csvfile:
        filewriter = csv.writer(csvfile, delimiter='\t',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
        filewriter.writerow(['CHROM', 'POS', 'REF', 'ALT', 'AF'])

"""Insert a single variant/frequency record into
the sqlite3 database"""
def insert_sqlite3(con, chrom, pos, ref, alt, af):
    cur = con.cursor()
    sqlstring = "insert into summary values ('"+ chrom + "' , " + str(pos) + " , '" + ref  + "' , '" + str(alt) +"', " + str(af) + " )"
    cur.execute(sqlstring)

"""Initialize sqlite3 table for storing genotype
frequencies"""
def create_table(con):
    cur = con.cursor()
    cur.execute("create table summary(chrom text, pos integer, ref text, alt text, af real)")

"""Print error to stderr"""
def print_error(hdr, msg):
    sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))

""" Main function to parse input cohort vcf into a DB file
and a tsv plain-text file"""
def parse_file(infile):
    counter = 0
    try:
        vcf_reader = vcf.Reader(open(infile, 'r'))
        conn = sqlite3.connect(r'SummaryDB.db')
        create_table(conn)
        createNewOutFile(outfile)

        # Iterate through records in vcf file
        for record in vcf_reader:
            counter += 1
            if not (counter % 5000):
                print_error("INFO", "Processing record {i}".format(i=counter))
            afs = extractAF(record.INFO)
            alleles = record.ALT

            # AF's vcf NUMBER is defined as 'A' in a conformant vcf
            # A mismatch of count is likely an error, in which case we
            # report the error and skip the row
            if len(alleles) != len(afs):
                print_error("INFO",
                    "{n_af} AF values found for {n_al} alleles in record {record}".format(
                    n_af=len(afs), n_al=len(alleles), record=record))

            # Write AF of alleles to outfile and DB
            with open(outfile, 'a') as csvfile:
                filewriter = csv.writer(csvfile, delimiter='\t',
                                         quotechar='|', quoting=csv.QUOTE_MINIMAL)

                for (al, af) in zip(alleles, afs):
                    filewriter.writerow([record.CHROM, record.POS, record.REF, al, af])
                    insert_sqlite3(conn, record.CHROM, record.POS, record.REF, al, af)

        # Commit the insert
        conn.commit()
        # Closing the connection to the database file
        conn.close()

    except IOError:
        print_error("Error", "There was an error reading file {fn}".format(fn=infile))
        sys.exit()

    except sqlite3.Error as er:
        print_error("Error", "SQLite3 error: {er}".format(er=er))

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'Usage: %s <input_file>' % sys.argv[0]
        print ' e.g. %s aggregate_file.vcf' % sys.argv[0]
        sys.exit()
    parse_file (sys.argv[1])