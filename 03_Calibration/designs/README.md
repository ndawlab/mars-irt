# Designs

This folder holds several files that contain information about item attributes and other various metadata used in the item structure models. 

## Data dictionaries

#### Item dimensionality (dimensionality.csv)

- item: the item in the MaRs-IB
- dimensionality score: item dimensionality, as defined in [Chierchia et al. (2019)](https://doi.org/10.1098/rsos.190232)

#### Item distractors (discractors.csv)

- item: the item in the MaRs-IB
- distractor: distractor type (MD-type or PD-type)
- d1: distance of the first distractor from the target response (in number of rules)
- d2: distance of the second distractor from the target response (in number of rules)
- d3: distance of the third distractor from the target response (in number of rules)

#### Item attributes (features.csv)

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

#### Person-level attribute (X1.csv)

- age: age of particpant
- gender: gender of participant (1 = female, 0 = other or rather not stay, -1 = male)
- rt_0: mean response time of participant
- rt_1: delta response time of participant

#### Item-level attributes (X2.csv)

- n_features: number of elements for an item clone
- n_rules: number of rules for an item clone
- distractor: distractor type (MD = 0.5, PD = -0.5) for an item clone
- rt: mean response time for an item clone

#### Item-to-clone mapping (X3.csv)

- indicates the mapping of clones (rows) to items (columns)