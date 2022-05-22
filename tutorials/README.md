# tutorials

This folder contains (1) the estimated item parameters from the item structure models; (2) the three MaRs-IB short forms tested in the validation study; and (3) a series of tutorials for using mixed integer programming for optimal test assembly.

## Organization

    ├── assembly.ipynb              <- Optimal test assembly tutorials using MIP.
    |
    ├── features.csv                <- MaRs-IB item attributes (see below).
    |
    ├── mars_sf1.csv                <- MaRs-IB short form #1 from manuscript.
    ├── mars_sf2.csv                <- MaRs-IB short form #2 from manuscript.
    ├── mars_sf3.csv                <- MaRs-IB short form #3 from manuscript.
    |
    ├── stats.csv                   <- Estimated item parameters from best-fitting model.

## Item attributes

Data dictionary for the item attributes file (`features.csv`). 

- item_id: the item clone identity in the MaRs-IB
- item: the item template identity in the MaRs-IB
- dimension: item dimensionality, as defined in [Chierchia et al. (2019)]
- shape_set: item clone variant
- shape_subset: membership of item clone (of one of nine total shape sets)
- distractor: distractor type (MD-type or PD-type)
- n_features: number of elements for that item
- fn_color: color change for nth element (0 = no change, 1 = change across row or column, 2 = change across both)
- fn_shape: shape change for nth element (0 = no change, 1 = change across row or column, 2 = change across both)
- fn_shape: shape change for nth element (0 = no change, 1 = change across row or column, 2 = change across both)
- fn_pos_tri: triangle position change for the nth element (0 = no change, 1 = change across row or column, 2 = change across both)
- fn_pos_row: row position change for the nth element (0 = no change, 1 = change across row or column, 2 = change across both)
- fn_size: size change for the nth element (0 = no change, 1 = change across row or column, 2 = change across both)- fn_pos_col: column position change for the nth element (0 = no change, 1 = change across row or column, 2 = change across both)