# An item response theory analysis of the MaRs-IB

Code and data for Zorowitz et al. (2023), "An item response theory analysis of the Matrix Reasoning Item Bank (MaRs-IB)". Behavior Research Methods. [https://doi.org/10.3758/s13428-023-02067-8](https://doi.org/10.3758/s13428-023-02067-8).

## Author
Sam Zorowitz (zorowitz [at] princeton.edu)

## Project Organization

The code for this project is divided across four branches:

    main (current branch)         <- all of the data and analysis code
    calibration                   <- software for the calibration experiment
    validation-A                  <- software for the validation experiment (short-forms)
    validation-B                  <- software for the validation experiment (long-forms)

The organization of the main branch (current branch) is as follows:

    ├── 01_Priors                   <- Data from pilot experiments.
    ├── 02_Design                   <- Parameter recovery studies for IRT models.
    ├── 03_Calibration              <- Data and code for the MaRs-IB calibration study. 
    ├── 04_Validation               <- Data and code for the MaRs-IB validation study. 
    ├── 05_Figures                  <- Figures for presentations & manuscript.
    ├── manuscript                  <- LaTeX code for the manuscript.
    ├── tutorials                   <- MaRs-IB item parameters, short forms, and optimal assembly tutorials.

## MaRs-IB Stimuli 

The actual stimuli of the MaRs-IB are publicly available at this [OSF repository](https://osf.io/g96f4/). 

## Acknowledgements

This project was made possible with support from the National Center for Advancing Translational Sciences (NCATS), a component of the National Institute of Health (NIH), under award number UL1TR003017.
