# Scripts

Scripts used for analysis. Described in the order in which they ought to be run.

## Descriptions

- Data collation (`collate_data.py`): collates the raw data into several CSVs
- Design matrices (`make_design.py`): makes the design matrices for the item response analyses.
- Item response models (`fit_irt.py`): fit an item response model using Stan.
- Posterior predictive checks & model comparison
  - Pareto smoothed importance sampling (`psis.py`)
  - Model comparison (`fit_irt_ppc.py`)
  - Chi-square discrepancy posterior predictive checks (`fit_irt_x2.py`)
  - SGDDM discrepancy posterior predictive checks (`fit_irt_sgddm.py`)
- Optimal test assembly (`assembly.py`): Support functions for test assembly.