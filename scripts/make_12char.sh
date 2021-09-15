#!/bin/bash

# Generate three column. 12-chaaracter labels and upload to an s3 bucket

set -e

if [[ -z "$1" ]]; then
    echo "usage $0 <s3-path>"
    echo "Example: "
    echo "$0 s3://uwlm-personal/ngh2/securelink"
    exit 1
fi

set -v
bucket="$1"
nfiles="${2-250}"

for i in 1 2 3 4; do

    dirname="threecol-12char-w${i}"
    tarball="securelink-12char-$(date '+%m-%d')-w$i.tgz"
    csvfile="securelink-12char-$(date '+%m-%d')-w$i.csv"

    if [[ -d "$dirname" ]]; then
        echo "$dirname already exists - remove it and try again"
        exit 1
    fi

    seq -w 1 $nfiles | \
	xargs -P 20 -I XXX barcoder threecol \
	      --dirname "$dirname" \
	      --code-length 12 \
	      --npages 30 \
	      --batch "$(date '+%m-%d')-w${i}-XXX" \
	      -o 'securelink-12char-{batch}-n{npages}.pdf'

    tar -czf "$tarball" "$dirname"/*.pdf
    aws s3 cp "$tarball" "$bucket/$tarball"
    cat "$dirname"/*.csv > "$csvfile"
    aws s3 cp "$csvfile" "$bucket/$csvfile"
done
