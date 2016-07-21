import argparse
import collections
import os

def _parse_args():
    '''Parse the input arguments.'''
    ap = argparse.ArgumentParser(description='Read input file and append frequency value')
    ap.add_argument('inputfile', help='The input VCF file')
    ap.add_argument('querydatabase', help='space separated database query files', nargs='+')
    return ap.parse_args()


def storedatabase(databasefile):
    '''Store the frequency of ALT from queried database'''
    outputdatabase=collections.defaultdict(int)
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
        alldatabasecontent[os.path.splitext(alldatabase_i)[0]]=tempcontent
    #####################
    ## read input file ##
    #####################
    inputfile=open(args.inputfile)
    inputlines=inputfile.xreadlines()
    for line in inputlines:
        linestrip=line.strip()
        if len(linestrip)>2:
            if linestrip[:2]=='##':
                ## print metadata header
                print linestrip
                continue
            elif linestrip[:2]=='#C':
                ## print additional metadata header
                for alldatabase_i in alldatabasecontent.keys():
                    print '##INFO=<ID={a},Number=A,Type=Float,Description="Allele frequency in {a} Cohort">'.format(a=alldatabase_i)
                ## print column header
                header=linestrip[1:].split('\t')
                print linestrip
            else:
                ## pair header with actual content
                zipinput=dict(zip(header,linestrip.split('\t')))
                currentcontent=zipinput['INFO']
                if currentcontent == ".":
                    currentcontent = ""
                for alldatabase_i in alldatabasecontent.keys():
                     # zero content INFO
                    if len(currentcontent)==0:
                        currentcontent=alldatabase_i+'='
                    # non-zero content INFO
                    else:
                        currentcontent=currentcontent+';'+alldatabase_i+'='
                    # get value and print out
                    all_value_ALT=[]
                     #prepare new info column
                    ALT_form=zipinput['ALT'].replace(' ','').split(',')
                    for ALT_i in ALT_form:
                        temp_value=get_alt_frequency(zipinput,alldatabasecontent,alldatabase_i,ALT_i)
                        all_value_ALT.append(temp_value)
                    currentcontent+=','.join(all_value_ALT)
                zipinput['INFO']=currentcontent
                print '\t'.join([zipinput[i] for i in header])