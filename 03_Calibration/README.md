# 03 Calibration Study

Data and code for the MaRs-IB calibration study.

## Project Organization

    ├── data                        <- Data from the calibration experiment.
    ├── designs                     <- Item attributes and other metadata for the item structure models. 
    ├── raw                         <- Raw data files from the calibrtion experiment.
    ├── scripts                     <- Scripts for data analysis.
    ├── stan_models                 <- Stan model code.
    ├── stan_results                <- Stan model fits, summaries, & diagnostics.
    |
    ├── 01_Screening.ipynb          <- Define and apply exclusion criteria.
    ├── 02_Descriptive.ipynb        <- Descriptive analyses of MaRs-IB response data.
    ├── 03_Modeling.ipynb           <- IRT analyses of MaRs-IB response data.
    ├── 04_Assembly.ipynb           <- Optimal test assembly using IRT model estimates. 
