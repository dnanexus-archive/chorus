###############################################
##SCRIPT BY  :  Ow Jack Ling
##CREATED    :  08 Jun 2016
##INPUT      :
##DESCRIPTION :
##ASSUMPTION : 1. Allele frequency(AF) fixed in the sub 2nd column of 8th field 
##D_VERSION    :  0.0.1
##P_VERSION: 1.0.0
##############################################

from __future__ import division
import csv
import sys
import argparse
import os

outfile = 'SummaryFile.txt'

def _parse_args():
    '''Parse the input arguments.'''
    ap = argparse.ArgumentParser(description='Read input file and append frequency value')
    ap.add_argument('inputfile', help='The input VCF file')
    return ap.parse_args()


"""Extract AF field from INFO"""
def extractAF(chr_p, all_p, cont_p ):
    all = map(int,all_p.split('/'))
    cont = map(int,cont_p.split('/'))

    if int(chr_p) >= 1 and int(chr_p) <= 22:
           calAF=(((all[2]-cont[2])*2)+(all[1]-cont[1])*1)/(((all[0]-cont[0])+(all[1]-cont[1])+(all[2]-cont[2]))*2) 
    elif chr_p =="Y":
            calAF=(((all[2]-cont[2]))+(all[1]-cont[1]))/(((all[0]-cont[0])+(all[1]-cont[1])+(all[2]-cont[2])))
    else:
            print_error("ERROR","Unable to calculate AF due to unknown number of male and female ") 
            sys.exit()

    return round(calAF, 5)

"""Print error to stderr"""
def print_error(hdr, msg):
    sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))

""" Main function to parse input cohort freq table into a DB file
and a tsv plain-text file"""
def parse_file( infile):

  counter = 0            

  file = open(infile, 'rb')

  data = csv.reader(file, delimiter='\t')

  print '\t'.join(['#CHR', 'POSITION', 'REF', 'ALT', 'FDB AF'])

  # loop each row 
  for row in data:
      counter = counter+1
      ## start after first column
      if counter ==1:
          continue 

      ## Extract AF in column 7
      AFvalues = extractAF(row[0], row[4], row[6])
      if AFvalues == 0:
           AFvalues = 0

      for (al) in row[3].split(','):
         ## Write Chrom, Pos, Ref, Alt, GT to a tsv file
         print '\t'.join(['chr'+row[0], str(row[1]), row[2], al, str(AFvalues)])


if __name__ == '__main__':

    ##################
    ## arg handling ##
    ##################
    args = _parse_args()

    parse_file (args.inputfile)

