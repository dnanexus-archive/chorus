# calculateAllelicFreq.py
# ------------------------
# Description:
# This script reads a VCF file that has an incomplete or missing AF data in the INFO field and populates an output text file with the allelic frequency
# of each alternate allele, along with its chromosome of origin, position within the chromosome, and the reference allele.
#
# Inputs:
# 1. Path to VCF file
# 2. Path to output text file
# 3. (Optional) Whether the allelic frequency should take into account missing alleles. Default: False.
# 		E.g. if a record had exactly two diploid samples, denoted '1/1' (homozygous alternate allele 1) and 'None' (missing alleles),
#		the default setting will produce an allelic frequency of 1.00 for the alternate allele,
#		while if missing alleles were to be accounted for, the allelic frequency will be 0.50 for the alternate allele.
#
# Output:
# 1. Output text file populated with allelic frequency. The output text file contains the following fields:
#		Chromosome  Position  Reference  Alternate  Allelic_Frequency
#
# Usage:
# 		python calculateAllelicFreq.py --vcf <path_to_VCF_file> --output <path_to_output_text_file> [--count_missing_alleles]
#
# General Strategy of Program:
# The script parses through each VCF record and creates a dictionary to store the number of times each alternate allele appears in
# a record. The allelic frequency of an alternate allele is then determined by dividing the number of times a specific alternate allele appears
# by the number of known alleles present in the record (or, if the count_missing_alleles option was selected, the total number of known and missing alleles present).
#
# Notes:
# 1. This script allows for the choice to include missing alleles in the VCF record in the allelic frequency calculations.
# 2. This script takes into account VCF records that use both '/' and '|' delimiters between the alleles. E.g. Both '0/0' and '1|0' formats are accepted.
# 3. This script also takes into account haploid calls (including but not limited to sex chromosomes where only one allele exists per chromosome).
# 4. This script parses VCF records with multiple alternate alleles and produces one line of allelic frequency output for each distinct alternate allele.
# 5. This script accepts both VCF files with and without 'chr'-labeled chromosome numbers and produces an output file with 'chr'-labeled chromosome numbers, 
#    assuming that the labeling convention is consistent within each VCF file.


import vcf
import sys
import argparse
import dxpy
import re


""" Parse command line arguments """
def parse_args():
	parser = argparse.ArgumentParser(description='This script reads in a VCF file without an AF ID field and generates a database output text file.',
									formatter_class=argparse.RawTextHelpFormatter)

	requiredNamed = parser.add_argument_group("Required named arguments")

	requiredNamed.add_argument('--vcf', '-v', metavar = "VCF_FILE",
						help='Path to input VCF file',
						required=True)

	requiredNamed.add_argument('--output', '-o', metavar = "OUTPUT_FILE",
						help='Path to output text file',
						required=True)

	requiredNamed.add_argument('--count_missing_alleles', action="store_true",
						help='This option takes into consideration missing alleles in the denominator when calculating allelic frequency (default: ignore missing alleles in the denominator)',
						required=False)

	return parser.parse_args()

"""Print error to stderr"""
def print_error(hdr, msg):
	sys.stderr.write("=={hdr}== {msg}\n".format(hdr=hdr, msg=msg))

"""Populate output file with Chromosome, Position, Reference Allele, Alternate Allele, and Alternate Allelic Frequency"""
def populate_output_file(ofile, vcf_file, count_missing_alleles):
	print ("Populating %s file with data fields: Chromosome, Position, Reference Allele, Alternate Allele, and Alternate Allelic Frequency." %ofile)

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
		name_has_chr = True
		record = next(vcf_reader)
		if record.CHROM.find('chr') == -1:
			name_has_chr = False
		
		write_allelic_freq(record, name_has_chr, count_missing_alleles, text_file)

		for record in vcf_reader:
			write_allelic_freq(record, name_has_chr, count_missing_alleles, text_file)
			
	except:
		print_error("Error", "There was an error reading the record format in the VCF file {fn}".format(fn=vcf_file))
		sys.exit()

	try:
		text_file.close()
	except IOError:
		print_error("Error", "There was an error closing file {fn}".format(fn=ofile))
		sys.exit()

"""Ensure that chromosome names have 'chr' as a prefix"""
def process_chrom(chrom, name_has_chr):
	if not name_has_chr:
		prefix = 'chr'
		chrom = prefix + chrom
	return chrom

def add_to_dict(allele_count_dict, allele):
	if allele in allele_count_dict:
		allele_count_dict[allele] += 1
	else:
		allele_count_dict[allele] = 1
	return allele_count_dict

"""Calculate and write allelic frequency of all alternate alleles in a record to output file"""
def write_allelic_freq(record, name_has_chr, count_missing_alleles, text_file):
	num_total_alleles = 0
	allele_count_dict = {}
	chromosome_name = process_chrom(record.CHROM, name_has_chr)

	is_haploid = False # Denotes the ploidy level of the allele
	for sample in record.samples:
		if not sample.gt_bases == None:
			num_total_alleles += 2
			split_bases = re.split(r'[|/]*', sample.gt_bases) # Works for VCFs using '|' and '/' as delimiters
			for allele in split_bases:
				allele_count_dict = add_to_dict(allele_count_dict, allele)
			if len(split_bases) == 1: # If there is only 1 allele, the variant call is haploid
				is_haploid = True
		else: # To-do: Take care of haploid calls that have to take into account missing alleles; what does it look like?
			if count_missing_alleles:
				num_total_alleles += 2

	if is_haploid: # Accounts for haploid calls
		num_total_alleles /= 2

	if (len(allele_count_dict) > 0 and record.REF in allele_count_dict): # Removes reference alleles from the dictionary.
		del allele_count_dict[record.REF]
	# else - if allele_count_dict has 1 or more alleles and none of them are the REF allele, continue. 

	try:
		for alt_allele in allele_count_dict:
			allelic_freq = (allele_count_dict[alt_allele]/(float(num_total_alleles)))
			text_file.write(" %s\t%s\t%s\t%s\t%f\n" %(chromosome_name, record.POS, record.REF, alt_allele, allelic_freq))
	except:
		print_error("Error", "There was an error writing to file {fn}".format(fn=ofile))
		sys.exit()

def main():
	args = parse_args()
	populate_output_file(args.output, args.vcf, args.count_missing_alleles)
	print "\n============== %s Successfully Populated ==============\n" %args.output

if __name__ == '__main__':
	main() 
