<!-- dx-header -->
# CHORUS Query (DNAnexus Platform App)

## Typical Usage
With the CHORUS app, users can understand the frequencies of observed variants in a variety of population cohorts in studies curated by the CHORUS project.

## What Does This App Do?
The CHORUS app queries variants (resolved by `CHROM`, `POS`, `REF`, and `ALT`) against curated frequency databases in the CHORUS database. The app writes variant frequencies from each cohort to the `INFO` column of the input VCF. The output VCF file will represent variants not found in a specific cohort with a period (`.`). The app will annotate genotype frequencies per `ALT` allele; for positions with multiple `ALT` alleles, frequencies will be given as a comma-separated list. The output VCF file's header will be largely the same as that of the input VCF file, with the addition of information about the CHORUS annotations.

### Input
The app uses a single VCF file generated from a typical secondary variant-calling pipeline as input.

### Output
The app returns a single annotated VCF file as output.

## Downstream Analysis
Users can view the annotated VCF file using common genome browsers, such as the BioDalliance browser supported by DNAnexus. Genotype frequencies appended by the CHORUS query can also be used as criteria for downstream filtering.