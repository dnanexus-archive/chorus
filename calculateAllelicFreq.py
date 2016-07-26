import vcf
import sys

outfile = 'output.txt'
vcffile = '/Users/plim-i/Documents/dx-toolkit/sg_fed_db/federated.db.2016.07.22.anonymized.vcf'

"""Print error to stderr"""
def print_error(hdr, msg):
    sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))

"""Populate output file with Chromosome, Position, Reference Allele, Alternate Allele, and Alternate Allelic Frequency"""
def populateOutputFile(ofile, vcf_file):
	try:
		text_file = open(ofile, "w")
		text_file.write("# CHROM\tPOS\tREF\tALT\tALLELIC_FREQ\n")

	except IOError:
		print_error("Error", "There was an error opening or writing to file {fn}".format(fn=ofile))
		sys.exit()

	try:
		vcf_reader = vcf.Reader(open(vcf_file, 'r'))

	except IOError:
		print_error("Error", "There was an error opening file {fn}".format(fn=vcf_file))
		sys.exit()

	try:
		for record in vcf_reader:
			for alt_index in xrange(len(record.ALT)):
				alt_allele = record.ALT[alt_index]
				allelic_freq = getAllelicFreq(record, alt_allele)
				chromosome_name = processChrom(record.CHROM)
			
				try:
					text_file.write(" %s\t%s\t%s\t%s\t%f\n" %(chromosome_name, record.POS, record.REF, alt_allele, allelic_freq))
				except IOError:
					print_error("Error", "There was an error writing to file {fn}".format(fn=ofile))
					sys.exit()	
	except:
		print_error("Error", "There was an error reading the VCF file format {fn}".format(fn=vcf_file))
    	sys.exit()

	try:
		text_file.close()
	except IOError:
		print_error("Error", "There was an error closing file {fn}".format(fn=ofile))
		sys.exit()		

"""Ensure that chromosome names have 'chr' as a prefix"""
def processChrom(chrom):
	if chrom.find('chr') == -1:
		prefix = 'chr'
	else:
		prefix = ''
		chrom = prefix + chrom

	return chrom

"""Calculate allelic frequency of specified alternate allele"""
def getAllelicFreq(record, alt_allele):
	num_total_alleles = 0
	num_alt_alleles = 0
	for sample_index in xrange(len(record.samples)):
		if not record.samples[sample_index].gt_bases == None:
			num_total_alleles += 2
			if (alt_allele == record.samples[sample_index].gt_bases.split("/")[0]):
				num_alt_alleles += 1
			if (alt_allele == record.samples[sample_index].gt_bases.split("/")[1]):
				num_alt_alleles += 1
	return (num_alt_alleles/(float(num_total_alleles)))

def main():
	populateOutputFile(outfile, vcffile)

if __name__ == '__main__':
	main()
