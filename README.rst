===================================================
barcoder: Barcode generation for securelink project
===================================================

Label Stock
===========

Prefer Avery stock.

* Three column format (1' x 2.5'): https://www.avery.com/blank/labels/94221
* Two column format (1 1/3' x 4'): https://www.avery.com/templates/5162
* Pool labels using 4 x 20 stock: https://www.avery.com/templates/94203

Installation
============

Installation into a virtualenv::

  git clone ...
  cd barcoder
  python3 -m py3-env
  source py3-env/bin/activate
  pip install -U pip
  pip install -e .

Usage
=====

Create a batch of 3 barcode files with 30 pages each in directory ``barcodes``::

  % barcoder threecol --dirname ./barcodes --npages 30 --nfiles 10 --batch 2020-05-27
  barcodes/securelink-3x10-2020-05-27-001-n30.pdf
  barcodes/securelink-3x10-2020-05-27-002-n30.pdf
  barcodes/securelink-3x10-2020-05-27-003-n30.pdf

Examples
========

These examples assume that you have the ``barcoder`` repo installed in
your home directory. I have been running this on gattaca.

To create batches of the three-column layout labels::

  cd ~/barcoder
  saml2aws login
  rm -r threecol*  # remove previous labels
  scripts/make_12char.sh

I have been producing pool labels like this (on gattaca)::

  cd ~/src/barcoder
  saml2aws login
  rm -r pool  # remove previous labels
  tarfile=pool-`ds`.tgz

  barcoder pool -d pool --nfiles 30 && \
  tar -cvf $tarfile pool/*.pdf && \
  aws s3 cp $tarfile "s3://uwlm-personal/ngh2/securelink/$tarfile"


