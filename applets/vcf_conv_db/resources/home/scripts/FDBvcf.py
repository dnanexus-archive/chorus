###############################################
##SCRIPT BY  :  Ow Jack Ling
##CREATED    :  14 Jun 2016
##INPUT      :
##DESCRIPTION :
##ASSUMPTION : 1. Allele frequency(AF) fixed in the sub 2nd column of 8th field 
##D_VERSION    :  0.0.1
##P_VERSION: 1.0.0
##############################################

import csv
import sqlite3

d1 = '\t'               # delimiter 1
#infile = 'GATK2011_Q50_Hg19_216samples_indel_filtered_merged.vcf'
outfile = 'SummaryFile.txt'

def extractAF( info):
    ## Extract AF in column 7
    Asub = info.split(';')
    AF = Asub[1].split('=')

    return  AF[1].split(',')

def createNewOutFile( ofile):
     ## Write Chrom, Pos, Ref, Alt, GT to a tsv file
     with open(ofile, 'w') as csvfile:
            filewriter = csv.writer(csvfile, delimiter='\t',
                                       quotechar='|', quoting=csv.QUOTE_MINIMAL)
            filewriter.writerow(['CHROM', 'POS', 'REF', 'ALT', 'AF'])

def insert_sqlite3(con, chr, pos, ref, alt, af):
    cur = con.cursor()

    sqlstring = "insert into summary values ('"+ chr + "' , " + pos + " , '" + ref  + "' , '" + alt +"', " + af + " )"

    cur.execute(sqlstring)

def create_table(con):
    cur = con.cursor()
    cur.execute("create table summary(chrom text, pos integer, ref text, alt text, af real)")



def parse_file( infile):

  counter = 0            

  try:
    file = open(infile, 'rb')

    data = csv.reader(file, delimiter='\t')

    conn = sqlite3.connect(r'SummaryDB.db')
	
    create_table(conn)
	
    createNewOutFile(outfile)

    # loop each row 
    for row in data:

      ## start after vcf header & metadata
      if '#' not in row[0]: 

        ## Extract AF in column 7
        AFvalues = extractAF(row[7])

        #Check for ',' (alt has multi allele)
        allele = row[4].split(',')
        #count = allele.len  + 1
            
        #print row[0]+d1+row[1]+d1+row[2]+d1+allele[alleleNo]+d1+AFvalues[alleleNo]
        #print allele.len
        for alleleNo in range(0, len(allele)):

          #print row[0]+d1+row[1]+d1+row[3]+d1+allele+d1+AFvalues
          #if alleleNo > 0:
          #   print row[0]+d1+row[1]+d1+row[2]+d1+allele[alleleNo]+d1+AFvalues[alleleNo]
      
          ## Write Chrom, Pos, Ref, Alt, GT to a tsv file
          with open(outfile, 'a') as csvfile:
               filewriter = csv.writer(csvfile, delimiter='\t',
                                       quotechar='|', quoting=csv.QUOTE_MINIMAL)
               filewriter.writerow([row[0], row[1], row[3], allele[alleleNo], AFvalues[alleleNo]])
			 
	  insert_sqlite3(conn, row[0], row[1], row[3], allele[alleleNo], AFvalues[alleleNo] )

    # Commit the insert 
    conn.commit()
	
    # Closing the connection to the database file
    conn.close()	  
	  
  except IOError:
         print "There was an error reading file"
         sys.exit()
  
  except sqlite3.Error as er:
    print 'er:', er.message


if __name__ == '__main__':
        from sys import argv, exit
        if len(argv) == 1:
            print 'Usage: %s <input_file>' % argv[0]
            print ' e.g. %s aggregate_file.vcf' % argv[0]
            exit()

        parse_file (argv[1])

        #import_sqllite3
