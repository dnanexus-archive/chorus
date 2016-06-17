###############################################
##SCRIPT BY  :  Ow Jack Ling
##CREATED    :  08 Jun 2016
##INPUT      :
##DESCRIPTION :
##ASSUMPTION :
##D_VERSION    :  0.0.1
##P_VERSION: 1.0.0
##############################################

import csv
import sqlite3
import sys
import getopt
import vcf

"""Write Chrom, Pos, Ref, Alt, GT to a tsv file"""
def createNewOutFile( ofile):
          ## Write Chrom, Pos, Ref, Alt, GT to a tsv file
          with open(ofile, 'w') as csvfile:
               filewriter = csv.writer(csvfile, delimiter='\t',
                                       quotechar='|', quoting=csv.QUOTE_MINIMAL)
               filewriter.writerow(['#CHR', 'POSITION', 'REF', 'ALT', 'FDB AF'])


""" Query sqlite3 db for the variant from vcf """
def query_db(con, chr, pos, ref, alt):

    cur = con.cursor()
    sqlstring = "select af from summary where chrom='"+ chr + "' and pos='" + str(pos) + "' and ref='" + ref  + "' and alt='" + str(alt) +"'"
    cur.execute(sqlstring)
    id_exists = cur.fetchone()

    if id_exists:
        return id_exists[0]
    else:
        return '.'

"""Print error to stderr"""
def print_error(hdr, msg):
       sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))


""" Main function to parse input cohort vcf and annotate into a Queried file"""
def parse_file(infile, dbfile, outfile):

    counter = 0
    check = False

    try:
        vcf_reader = vcf.Reader(open(infile,'r'))

        conn = sqlite3.connect(dbfile)
        curMeta = conn.cursor()
        createNewOutFile(outfile)

        # loop each row
        for record in vcf_reader:

          counter += 1
          if not (counter % 5000):
              print_error("INFO","Processing record {i}".format(i=counter))

          ## check for chr in chromosome field
          if check == False:
               if record.CHROM.find('chr') == -1:
                   Prefix = 'chr'
               else:
                   Prefix = ''

               check = True

          allele = record.ALT
          chr = Prefix + record.CHROM

          ## Write Chrom, Pos, Ref, Alt, AF to a tsv file
          with open(outfile, 'a') as csvfile:
            filewriter = csv.writer(csvfile, delimiter='\t',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)


            for al in allele:
                dbAF = query_db(conn, chr, record.POS, record.REF, al)
                filewriter.writerow([chr, record.POS, record.REF, al, dbAF])

        # Closing the connection to the database file
        conn.close()


    except IOError:
         print_error("Error", "There was an error reading file {fn}".format(fn=infile))
         sys.exit()

    except sqlite3.Error as er:
         print_error("Error", "SQLite3 error: {er}".format(er=er))
         conn.close()
         sys.exit()


if __name__ == '__main__':
    from sys import argv, exit
    if len(argv) == 1:
        print 'Usage: %s -i <input_file> -d <sqlite db file> -o <output_file>' % argv[0]
        print ' e.g. %s -i aggregate_file.vcf -d frequency.db -o frequencies.txt' % argv[0]
        exit()

    # TODO: Suggest move to argparse for more modern argument parsing
    # and safeguarding against unspecified non-optional parameters
    args = {}

    opts, extraparams = getopt.getopt(sys.argv[1:], "i:d:o:")

    for o,p in opts:
        if o == '-i':
            args["input"] = p
        elif o == '-d':
            args["db"] = p
        elif o == '-o':
            args["output"] = p

    parse_file (args["input"], args["db"], args["output"])
