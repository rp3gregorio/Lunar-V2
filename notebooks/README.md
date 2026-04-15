# Notebooks

Exploratory Jupyter notebooks. Not authoritative — anything worth
reproducing should move into `lunar/` or `tests/` eventually.

Suggested order (once modules are wired up):

1. `01_grid_and_properties.ipynb` — visualize `density_hayne`,
   `conductivity_hayne`, `conductivity_martinez`, and
   `conductivity_icy` at a few representative temperatures and
   depths. Sanity-check the geometric grid.
2. `02_equatorial_benchmark.ipynb` — reproduce the Vasavada (2012) /
   Williams (2017) equatorial diurnal curve (`T_max ~ 390 K`,
   `T_min ~ 95 K`).
3. `03_apollo_validation.ipynb` — Apollo 15 / 17 subsurface temperature
   at 1 m (~252 / 255 K).
4. `04_south_pole_patch.ipynb` — drive the pipeline on a 10 × 10 km
   LDEM subset at a candidate Artemis landing site.
5. `05_ice_feedback.ipynb` — show the z_star convergence of the
   ice-coupled iteration loop.
