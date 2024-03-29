#!/usr/bin/bash
#
# Script to compress and copy folders generated by the convert_logs_to_json_for_insights_s3.py
# program to the S3 target folder in BFD-Insights AWS S3.
#
# This copies all "dt=*/" type folders from the current PWD directory to the target S3 folder.
#
# Provide S3 target path as the $1 command line arg. NOTE: Include the trailing "/" on the S3 path.
#
# Example:
#
# $ sh ../upload_folders_to_s3.sh s3://<S3 bucket>/databases/bb2/
#
# NOTE: You must source the BFD AWS credentials in to your shell before running this!
#
for dir in $(ls -d events-*)
do
  echo "==="
  echo GZIP FILES IN:  ${dir}
  echo
  find ${dir} -type f -exec gzip {} \;
  echo
  echo "==="
  echo
  echo "==="
  echo COPYING TO S3: ${dir}
  echo
  aws s3 cp "${dir}" "${1}${dir}" --recursive
  echo
  echo "==="
done
