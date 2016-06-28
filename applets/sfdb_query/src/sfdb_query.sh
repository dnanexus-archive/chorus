#!/bin/bash

set -e -x -o pipefail

main() {

    dx-download-all-inputs

    if [[ "$DX_RESOURCES_ID" != "" ]]; then
      DX_ASSETS_ID="$DX_RESOURCES_ID"
    else
      DX_ASSETS_ID="$DX_PROJECT_CONTEXT_ID"
    fi

    cohorts=$(dx ls $DX_ASSETS_ID --folder)
    summaryfile_name="summaryfile.txt"
    # We don't quote $cohorts to enable split by whitespace
    # Cohort names CANNOT contain whitespace, or unexpected
    # behavior may result
    for cohort in $cohorts; do

        # Remove trailing / in folder name
        cohort_name="${cohort%/}"
        echo "Processing cohort: ${cohort%/}"

        db_file=$(dx find data --name $summaryfile_name --path $DX_ASSETS_ID:/$cohort --brief)

        if [ -z $db_file ]; then
            dx-jobutil-report-error "Could not find $summaryfile_name file for cohort $cohort_name" AppError
        fi

        if [ -f "$cohort_name.txt" ]; then
            dx-jobutil-report-error "The cohort name $cohort_name is not unique" AppError
        fi

        variant_db="$cohort_name.txt"
        dx download "$db_file" -o "$variant_db"

        db_build=$(dx describe "$db_file" --json | jq -r .properties.build)

        if [ -z $db_build ]; then
            dx-jobutil-report-error "Build not specified in the db for $cohort_name" AppError
        fi

        if [[ "$build" != "$db_build" ]]; then
            dx-jobutil-report-error "The build specified for the query ($build) differs from the build of the database ($db_build)" AppError
        fi

        python /home/scripts/AnnotateFDB.py "$input_vcf_path" "$variant_db" >  "$cohort_name.tsv"
    done

    if [ -z "$output_fn" ]; then
        output_fn="${input_vcf_prefix}"
    fi

    mkdir -p out/annotated_vcf

    python /home/scripts/VCF_info_appending.py "$input_vcf_path" *.tsv > "out/annotated_vcf/${output_fn}.annotated.vcf"

    dx-upload-all-outputs

}
