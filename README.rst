===================================================
barcoder: Barcode generation for securelink project
===================================================

Label Stock
===========

Prefer Avery stock.

* Three column format (1' x 2.5'): https://www.avery.com/blank/labels/94221
* Two column format (1 1/3' x 4'): https://www.avery.com/templates/5162

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

