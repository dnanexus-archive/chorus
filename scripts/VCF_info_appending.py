
import collections
import argparse

## unused
#import vcf
#inputfile=vcf.Reader(open('RAI_128_R1.Hf.filtered.vcf.txt','r'))

def _parse_args():
    '''Parse the input arguments.'''
    ap = argparse.ArgumentParser(description='Read input file and append frequency value')
    ap.add_argument('inputfile', help='The input VCF file')
    ap.add_argument('querydatabase', help='space separated database query files', nargs='+')
    return ap.parse_args()


def storedatabase(databasefile):
    outputdatabase=collections.defaultdict(int)
    fdd=open(databasefile)
    lines=fdd.readlines()
    for line in lines[:10]:
        temp=line.strip().split()
        outputdatabase[str(temp[0])+'_'+str(temp[1])]=str(temp[4])
    return outputdatabase


if __name__ == '__main__':
    
    ##################
    ## arg handling ##
    ##################
    args = _parse_args()
    alldatabase=args.querydatabase

    ####################
    ## store database ##
    ####################   
    alldatabasecontent={}
    for alldatabase_i in alldatabase:
        tempcontent=storedatabase(alldatabase_i)
        alldatabasecontent[alldatabase_i]=tempcontent   
    
    #####################
    ## read input file ##
    #####################
    inputfile=open(args.inputfile)
    inputlines=inputfile.xreadlines()
    for line in inputlines:
        linestrip=line.strip()
        if len(linestrip)>2:
            ## print header
            if linestrip[:2]=='##':
                print linestrip
                continue
            elif linestrip[:2]=='#C':
                print linestrip
                header=linestrip[1:].split('\t')
            else:             ## pair header with actual content
                zipinput=dict(zip(header,linestrip.split('\t')))
                currentcontent=zipinput['INFO']
                # get value and print out
                temp_value=''
                for alldatabase_i in alldatabase:
                    if zipinput['CHROM']+'_'+zipinput['POS'] in alldatabasecontent[alldatabase_i]:
                        temp_value=alldatabasecontent[alldatabase_i][zipinput['CHROM']+'_'+zipinput['POS']]
                    else:
                        temp_value='NA'
                    if len(currentcontent)==0:      # zero content INFO
                        currentcontent=alldatabase_i+'='+temp_value
                    else:
                        currentcontent=currentcontent+','+alldatabase_i+'='+temp_value
                zipinput['INFO']=currentcontent
                print '\t'.join([zipinput[i] for i in header])