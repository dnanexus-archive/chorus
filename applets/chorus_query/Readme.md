<!-- dx-header -->
# CHORUS Query (DNAnexus Platform App)

This public-facing app is responsible for receiving a vcf file, querying multiple cohort databases in a federated way, and annotating genotype frequencies of cohorts to the original input vcf.

### Typical Usage
With a VCF file generated from a typical secondary variant-calling pipeline, one want to understand the frequencies of observed variants in a variety of population cohorts in studies curated by the Singapore Federated Database project.

### What does this app do
From the input VCF, variants (resolved by CHROM, POS, REF and ALT) are queried against curated frequency databases in CHORUS. Frequencies for variant in each cohort is written to the INFO column of the input VCF. Corresponding header specification will be added to the VCF file. For variants which are not found in a specific cohort, its frequency will be represented using a period (".") in the output VCF. Genotype frequencies will be annotated per ALT allele; in positions with multiple ALT alleles, frequencies will be given as a comma-separated list.

### Output file
A single annotated VCF file will be returned as the output.

### Downstream analysis
The annotated VCF file can be viewed  using common genome browser, such as the BioDalliance browser supported by DNAnexus. Genotype frequencies appended by the CHORUS query can also be used as a criteria for downstream filtering.
