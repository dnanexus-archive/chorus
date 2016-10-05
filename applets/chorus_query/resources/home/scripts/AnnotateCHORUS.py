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
import argparse
import sys
import vcf
import os
import collections

def _parse_args():
    '''Parse the input arguments.'''
    ap = argparse.ArgumentParser(description='Read input file and append frequency value')
    ap.add_argument('inputfile', help='The input VCF file')
    ap.add_argument('querydatabase', help='space separated database query files', nargs='+')
    return ap.parse_args()


"""Write Chrom, Pos, Ref, Alt, GT to a tsv file"""
def createNewOutFile( ofile):
          ## Write Chrom, Pos, Ref, Alt, GT to a tsv file
          with open(ofile, 'w') as csvfile:
               filewriter = csv.writer(csvfile, delimiter='\t',
                                       quotechar='|', quoting=csv.QUOTE_MINIMAL)
               filewriter.writerow(['#CHR', 'POSITION', 'REF', 'ALT', 'FDB AF'])

def storedatabase(databasefile):
    '''Store the frequency of ALT from queried database'''
    outputdatabase={}
    fdd=open(databasefile)
    lines=fdd.readlines()
    for line in lines:
        if line and line[0] == '#':
            continue

        temp=line.strip().split('\t')
        outputdatabase['_'.join(map(str,temp[0:4]))]=str(temp[4])
    return outputdatabase

def get_alt_frequency(zipinput_p,alldatabasecontent_p,alldatabase_i_p,ALT_form_p):
    '''Return frequency of ALT from dict (from queried database)'''
    if zipinput['CHROM']+'_'+zipinput_p['POS']+'_'+zipinput_p['REF']+'_'+ALT_form_p in alldatabasecontent_p[alldatabase_i_p]:
        temp_return=alldatabasecontent_p[alldatabase_i_p][zipinput_p['CHROM']+'_'+zipinput_p['POS']+'_'+zipinput_p['REF']+'_'+ALT_form_p]
    else:
        temp_return='.'
    return temp_return



"""Print error to stderr"""
def print_error(hdr, msg):
       sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))


""" Main function to parse input cohort vcf and annotate into a Queried file"""
def parse_file(infile, alldatabase):

    counter = 0
    check = False
    outfile = 'vcf.txt'

    ####################
    ## store database ##
    ####################
    alldatabasecontent={}
    for alldatabase_i in alldatabase:
        #print alldatabase_i
        tempcontent=storedatabase(alldatabase_i)
        alldatabasecontent=tempcontent


    try:
        vcf_reader = vcf.Reader(open(infile,'r'))

        createNewOutFile(outfile)
        print '\t'.join(['#CHR', 'POSITION', 'REF', 'ALT', 'FDB AF'])
        
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
                str1 = str(chr) + "_" + str(record.POS) + "_" +   str(record.REF) + "_" + str(al) 
                if str1 in alldatabasecontent:
                     dbAF = alldatabasecontent[str1]
                else:
                     dbAF = '.'
               
                print '\t'.join(map(str,[chr,record.POS,record.REF,al,dbAF]))
                #filewriter.writerow([chr, record.POS, record.REF, al, dbAF])

    except IOError:
         print_error("Error", "There was an error reading file {fn}".format(fn=infile))
         sys.exit()



if __name__ == '__main__':


    ##################
    ## arg handling ##
    ##################
    args = _parse_args()
    alldatabase=args.querydatabase

    parse_file (args.inputfile, alldatabase)
