#!/bin/bash

set -e -o pipefail

print_summary() {
    declare -a annotated=("${!1}")
    declare -a unannotated=("${!2}")
    echo "==================CHORUS Summary================="
    echo "Annotated query against the following cohorts:"
    echo "${annotated[@]}"
    echo "Following cohorts were not annotated:"
    echo "${unannotated[@]}"
    echo "==============End of CHORUS Summary============="
}

main() {
    dx-download-all-inputs

    if [[ "$DX_RESOURCES_ID" != "" ]]; then
      DX_ASSETS_ID="$DX_RESOURCES_ID";
    else
      DX_ASSETS_ID="$DX_PROJECT_CONTEXT_ID";
    fi

    # Check if the input_vcf file is suspicious
    # Quit the job if the query VCF contains variants are continuous (when the median of the loci gap are <=10bp apart from each other) 
    #
    cat $input_vcf_path | vcf-sort > ${input_vcf_prefix}_sorted.vcf

    distribution_output="/home/dnanexus/${input_vcf_prefix}.txt"

    vcf_stats=($(awk -v output_fn=$distribution_output '
      BEGIN {
        rownum=0; lessthantennum=0; prechr="NA";sum=0
      } 
      ($0 !~ /^\#/){if ($1==prechr) {
        diff = $2-prepos;
        print diff >> output_fn
        if (diff <= 10) lessthantennum+=1};
        prechr=$1; prepos=$2; rownum+=1; sum+=diff
      }
      END {
        print lessthantennum,lessthantennum/rownum,sum/rownum
      }
      ' "${input_vcf_prefix}_sorted.vcf" ))

    lessthantennum=${vcf_stats[0]}
    continuous_precentage=${vcf_stats[1]}
    continuous_mean=${vcf_stats[2]}

    gap_median=$(cat /home/dnanexus/${input_vcf_prefix}.txt | sort -k1,1n |
    awk '{ count[NR] = $1;}
     END {
     if (NR % 2){
       print count[(NR + 1) / 2];
     } else { print (count[(NR / 2)] + count[(NR / 2) + 1]) / 2.0; }
    }' )
  
    if [[ $(echo "${gap_median} <= 10" | bc -l ) -eq 1 ]]; then
        echo "Terminated job because suspicious VCF file ${input_vcf_name} detected. Please contact CHORUS administrators (owjl@gis.a-star.edu.sg) if you have any questions."; exit 1;
    fi

    cohorts=$(dx ls $DX_ASSETS_ID --folder)
    summaryfile_name="summaryfile.txt"

    local annotated_cohorts=()
    local unannotated_cohorts=()

    # We don't quote $cohorts to enable split by whitespace
    # Cohort names CANNOT contain whitespace, or unexpected
    # behavior may result
    for cohort in $cohorts; do
        # Running on control cohorts ONLY
        if [[ $cohort == CTR* ]]; then
        # Remove trailing / in folder name
            cohort_name="${cohort%/}"
            echo "Processing cohort: ${cohort%/}"

            db_file=$(dx find data --name $summaryfile_name --property build=$build --path $DX_ASSETS_ID:/$cohort --brief)

            # Could not find the corresponding build summary_file.txt
            if [[ -z $db_file ]]; then
                echo "Could not find $summaryfile_name file for cohort $cohort_name for build $build"
                unannotated_cohorts+=("$cohort_name")
                continue
            fi

            if [[ -f "$cohort_name.txt" ]]; then
                dx-jobutil-report-error "The cohort name $cohort_name is not unique" AppError
            fi

            variant_db="$cohort_name.txt"
            dx download "$db_file" -o "$variant_db"

            python /home/scripts/AnnotateCHORUS.py "$input_vcf_path" "$variant_db" >  "$cohort_name.tsv"
            annotated_cohorts+=("$cohort_name")
        fi
    done

    if [[ -z "$output_fn" ]]; then
        output_fn="${input_vcf_prefix}"
    fi

    mkdir -p out/annotated_vcf

    python /home/scripts/VCF_info_appending.py "$input_vcf_path" *.tsv > "out/annotated_vcf/${output_fn}.annotated.vcf"

    print_summary annotated_cohorts[@] unannotated_cohorts[@]

    dx-upload-all-outputs
}