#!/bin/bash

set -e -x -o pipefail

print_summary() {
    declare -a annotated=("${!1}")
    declare -a unannotated=("${!2}")
    echo "================SGFD Summary=================="
    echo "Annotated query against the following cohorts:"
    printf '%s\n' "${annotated[@]}"
    echo "Following cohorts were not annotated:"
    printf '%s\n' "${unannotated[@]}"
    echo "==============End of SGFD Summary============="
}

main() {

    dx-download-all-inputs

    if [[ "$DX_RESOURCES_ID" != "" ]]; then
      DX_ASSETS_ID="$DX_RESOURCES_ID"
    else
      DX_ASSETS_ID="$DX_PROJECT_CONTEXT_ID"
    fi

    cohorts=$(dx ls $DX_ASSETS_ID --folder)
    summaryfile_name="summaryfile.txt"

    annotated_cohorts=()
    unannotated_cohorts=()

    # We don't quote $cohorts to enable split by whitespace
    # Cohort names CANNOT contain whitespace, or unexpected
    # behavior may result
    for cohort in $cohorts; do

        # Remove trailing / in folder name
        cohort_name="${cohort%/}"
        echo "Processing cohort: ${cohort%/}"

        db_file=$(dx find data --name $summaryfile_name --property build=$build --path $DX_ASSETS_ID:/$cohort --brief)

        # Could not find the corresponding build summary_file.txt
        if [ -z $db_file ]; then
            echo "Could not find $summaryfile_name file for cohort $cohort_name for build $build"
            unannotated_cohorts+=("$cohort_name")
            continue
        fi

        if [ -f "$cohort_name.txt" ]; then
            dx-jobutil-report-error "The cohort name $cohort_name is not unique" AppError
        fi

        variant_db="$cohort_name.txt"
        dx download "$db_file" -o "$variant_db"

        python /home/scripts/AnnotateFDB.py "$input_vcf_path" "$variant_db" >  "$cohort_name.tsv"
        annotated_cohorts+=("$cohort_name")

    done

    if [ -z "$output_fn" ]; then
        output_fn="${input_vcf_prefix}"
    fi

    mkdir -p out/annotated_vcf

    python /home/scripts/VCF_info_appending.py "$input_vcf_path" *.tsv > "out/annotated_vcf/${output_fn}.annotated.vcf"

    print_summary annotated_vcf[@] unannotated_cohorts[@]

    dx-upload-all-outputs
}
