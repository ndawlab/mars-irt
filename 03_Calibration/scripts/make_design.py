import os, sys
import numpy as np
from os.path import dirname
from pandas import read_csv
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Model parameters.
design = int(sys.argv[1])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare item feature matrix.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load item features.
features = read_csv(os.path.join(ROOT_DIR, 'data', 'features.csv'), index_col='item')

## Design 0: intercept only.
if design == 0:
    
    ## Define intercept.
    features['x0'] = 1
    
## Design 1: number of total rules.
elif design == 1:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    features['x1'] = np.where(features.filter(regex='f[1-4]') > 0, 1, 0).sum(axis=1)
        
## Design 2: number of total rules (by type).
elif design == 2:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    features['x1'] = np.where(features.filter(regex='f[1-4]') == 1, 1, 0).sum(axis=1)
    features['x2'] = np.where(features.filter(regex='f[1-4]') == 2, 1, 0).sum(axis=1)
    
## Design 3: number of total rules (by feature).
elif design == 3:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    for i, col in enumerate(['color$','shape$','tri$','pos_[r,c]','size$']):
        features[f'x{i+1}'] = np.where(features.filter(regex=col) > 0, 1, 0).sum(axis=1)
    
## Design 4: number of total rules (by type & feature).
elif design == 4:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    for i, col in enumerate(['color$','shape$','tri$','pos_[r,c]','size$']):
        features[f'x{2*i+1}'] = np.where(features.filter(regex=col) == 1, 1, 0).sum(axis=1)
        features[f'x{2*i+2}'] = np.where(features.filter(regex=col) == 2, 1, 0).sum(axis=1)
    
## Design 5: number of total rules (by type & feature) + distractor.
elif design == 5:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    for i, col in enumerate(['color$','shape$','tri$','pos_[r,c]','size$']):
        features[f'x{2*i+1}'] = np.where(features.filter(regex=col) == 1, 1, 0).sum(axis=1)
        features[f'x{2*i+2}'] = np.where(features.filter(regex=col) == 2, 1, 0).sum(axis=1)
        
    ## Define distractor-based regressors.
    features['x11'] = np.where(features.distractor == 'md', 1, 0) 
    
## Design 6: number of total rules (by type & feature) + distractor + perceptual elements.
elif design == 6:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    for i, col in enumerate(['color$','shape$','tri$','pos_[r,c]','size$']):
        features[f'x{2*i+1}'] = np.where(features.filter(regex=col) == 1, 1, 0).sum(axis=1)
        features[f'x{2*i+2}'] = np.where(features.filter(regex=col) == 2, 1, 0).sum(axis=1)
        
    ## Define distractor-based regressors.
    features['x11'] = np.where(features.distractor == 'md', 1, 0)
    
    ## Define percept-based regressors.
    for i, j in enumerate(range(2,10)): 
        features[f'x{12+i}'] = np.where(features.shape_subset == j, 1, 0)
    
else:
    
    raise ValueError(f'design type "{design}" not available.')
    
## Extract regressors.
X = features[features.filter(regex='x[0-9]').columns].values

## Save.
np.savetxt(os.path.join(ROOT_DIR, 'designs', f'x{design}.txt'), X, fmt='%0.0f', delimiter=',')