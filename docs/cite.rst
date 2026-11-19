How to cite GaiaXPy
===================

If you use GaiaXPy in your research, cite the DOI for the software release. The DOIs are listed below.

For DR3 synthetic photometry, also cite `Gaia Collaboration, Montegriffo et al. (2023), A&A, 674, A33 <https://doi.org/10.1051/0004-6361/202243709>`_.

Further references will be added to this section, including a citation for the GaiaXPy paper.

Identify the version and scientific references
----------------------------------------------

For results that include output metadata, use the recorded ``gaiaxpy_version``
to identify the package version that produced the result. The metadata also
records the configuration files used in the calculation and their bibliographic
references where supplied. Consult those references when citing the models,
filters or corrections used in the analysis.

For a returned DataFrame named ``data``, the metadata is available in
``data.attrs['gaiaxpy_metadata']``. For saved results, use the function
``read_output_metadata`` from ``gaiaxpy.output``. For CSV results, it reads the
companion metadata file. See :doc:`usage` for an example.

To check the version installed in the current environment, run:

.. code-block:: python

   import gaiaxpy

   print(gaiaxpy.__version__)

DOIs
----
* **DOI v2.2.0**: 10.5281/zenodo.24356606

* **DOI v2.1.5**: 10.5281/zenodo.23400597

* **DOI v2.1.4**: 10.5281/zenodo.17943031

* **DOI v2.1.3**: 10.5281/zenodo.17879827

* **DOI v2.1.2**: 10.5281/zenodo.11617977

* **DOI v2.1.1**: 10.5281/zenodo.11108915

* **DOI v2.1.0**: 10.5281/zenodo.8239995

* **DOI v2.0.1**: 10.5281/zenodo.7566303

* **DOI v2.0.0**: 10.5281/zenodo.7524744

* **DOI v1.2.4**: 10.5281/zenodo.7515812

* **DOI v1.2.3**: 10.5281/zenodo.7374213

* **DOI v1.2.2**: 10.5281/zenodo.7347904

* **DOI v1.2.1**: 10.5281/zenodo.7244380

* **DOI v1.2.0**: 10.5281/zenodo.7015044

* **DOI v1.1.4**: 10.5281/zenodo.6674521

* **DOI v1.1.3**: 10.5281/zenodo.6653044

* **DOI v1.1.2**: 10.5281/zenodo.6642313

* **DOI v1.1.1**: 10.5281/zenodo.6637762

* **DOI v1.1.0**: 10.5281/zenodo.6624491

* **DOI v1.0.2**: 10.5281/zenodo.6569912

* **DOI v1.0.0**: 10.5281/zenodo.6563093
