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

d1 = '\t'               # delimiter 1
#infile = 'GATK2011_Q50_Hg19_216samples_indel_filtered_merged.vcf'
outfile = 'resultfile.txt'



"""Write Chrom, Pos, Ref, Alt, GT to a tsv file"""
def createNewOutFile( ofile):
          ## Write Chrom, Pos, Ref, Alt, GT to a tsv file
          with open(ofile, 'w') as csvfile:
               filewriter = csv.writer(csvfile, delimiter='\t',
                                       quotechar='|', quoting=csv.QUOTE_MINIMAL)
               filewriter.writerow(['CHR', 'POSITION', 'REF', 'ALT', 'FDB AF'])


"""Print error to stderr"""
def print_error(hdr, msg):
       sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))


""" Main function to parse input cohort vcf and annotate into a Queried file"""
def parse_file( infile, build):

  counter = 0            
  check = False

  try:
    vcf_reader = vcf.Reader(open(infile,'r'))

    conn = sqlite3.connect('SummaryDB.db')
    curMeta = conn.cursor()
    curMeta.execute("SELECT build FROM cohort_metadata where build =:id ", {"id": build} )
    conn.commit()
    row = curMeta.fetchall()
    ## check for same build in metadata table
    if len(row) == 0:
        msg='ERROR: Build ' + build + ' do not match with the build in variant database'
	# exit code with error message
        print(msg)
        sys.exit()
	
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

            
      ## Write Chrom, Pos, Ref, Alt, GT to a tsv file
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

""" Query sqlite3 db for the variant from vcf """		 
def query_db(con, chr, pos, ref, alt):

        #conn = sqlite3.connect('SummaryDB.db')

        cur = con.cursor() 

        sqlstring = "select af from summary where chrom='"+ chr + "' and pos='" + str(pos) + "' and ref='" + ref  + "' and alt='" + str(alt) +"'"
	
	cur.execute(sqlstring)
	              		  
	id_exists = cur.fetchone()
	
	if id_exists:
		return id_exists[0]
	else:
		return '.'
		
	# Closing the connection to the database file
        #conn.close()


if __name__ == '__main__':        
        from sys import argv, exit		
        if len(argv) == 1:
            print 'Usage: %s -b <build> -i <input_file>' % argv[0]
            print ' e.g. %s -b hg38 -i aggregate_file.vcf' % argv[0]
            exit()
			
        args = {}

        opts, extraparams = getopt.getopt(sys.argv[1:], "b:i:")
		
	for o,p in opts:
                if o == '-b':
                     args[ "build" ] = p
		elif o == '-i':
                     args[ "input" ] = p

        print args["input"]
        print args["build"]

        parse_file (args["input"], args["build"])


