# Software and asset notices

Application code is provided under the repository's MIT LICENSE. Dependencies and separately obtained assets retain their own ownership and license terms. The application license does not relicense the LIC-DSF template or any user workbook.

The declared direct runtime dependencies are the pinned public `excel-grapher` revision, `openpyxl`, `numpy`, `PyYAML`, `matplotlib` and the tested `fastpyxl` version. The exact versions are in `pyproject.toml`; the installed calculation identity records the evaluator revision and relevant numerical dependency versions. Do not silently replace them when reproducing results.

Matplotlib renders charts with its distributed DejaVu Sans font. No separate proprietary font file or private brand asset is required. A binary distribution must retain the complete license and notice files supplied by its Python runtime, wheels, fonts and bundled libraries. Wheel contents and dependency closure require inspection for each target platform; a source dependency declaration is not a complete binary notice inventory.

The official World Bank IDA21 template is downloaded separately from the publisher. The general source distribution includes no workbook binary. Its Ghana-labelled sample values are purely illustrative and must not be presented as an official Ghana forecast or DSA. User-provided analytical data remain outside the software's source distribution and have their own sharing restrictions.

Before release, retain a versioned inventory of exact runtime archives and wheels, publisher provenance, hashes, bundled license files and any redistribution conditions. Record unresolved asset rights as a release gap rather than assuming that availability for download grants redistribution rights.
