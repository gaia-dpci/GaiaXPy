"""Read spectrum files into pandas DataFrames.

The parsers share readers for CSV, ECSV, FITS and XML/VOTable files.
Specialised parsers handle continuous mean spectra, sampled spectra, and inverse-basis tables.

CSV, ECSV, FITS and XML inputs may be gzip compressed. They are
read through a stream without saving a decompressed copy. XML input must
contain a VOTable.

Some AVRO support is also available, but this is not a format distributed
by the Archive, and is intended for internal use only.

These parsers are normally selected by :mod:`gaiaxpy.input_reader`, which
supplies the required columns and performs input normalisation, release
checks and coefficient corrections.
"""
