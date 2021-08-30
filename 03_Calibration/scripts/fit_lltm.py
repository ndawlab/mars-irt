import os, sys
import numpy as np
from os.path import dirname
from pandas import read_csv
from cmdstanpy import CmdStanModel
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = sys.argv[1]

## Model parameters.
contrast = int(sys.argv[2])

## Sampling parameters.
iter_warmup   = 5000
iter_sampling = 2500
chains = 4
thin = 1
parallel_chains = 4

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'data.csv'))

## Apply rejections.
reject = read_csv(os.path.join(ROOT_DIR, 'data', 'reject.csv'))
data = data.loc[data.subject.isin(reject.query('reject==0').subject)]

## Drop missing data.
data = data.dropna()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare item feature matrix.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load item features.
features = read_csv(os.path.join(ROOT_DIR, 'data', 'features.csv'), index_col='item')

## Contrast 0: intercept only.
if contrast == 0:
    
    ## Define intercept.
    features['x0'] = 1
    
## Contrast 1: number of total rules.
elif contrast == 1:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    features['x1'] = np.where(features.filter(regex='f[1-4]') > 0, 1, 0).sum(axis=1)
        
## Contrast 2: number of total rules (by type).
elif contrast == 2:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    features['x1'] = np.where(features.filter(regex='f[1-4]') == 1, 1, 0).sum(axis=1)
    features['x2'] = np.where(features.filter(regex='f[1-4]') == 2, 1, 0).sum(axis=1)
    
## Contrast 3: number of total rules (by feature).
elif contrast == 3:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    for i, col in enumerate(['color$','shape$','tri$','pos_[r,c]','size$']):
        features[f'x{i+1}'] = np.where(features.filter(regex=col) > 0, 1, 0).sum(axis=1)
    
## Contrast 4: number of total rules (by type & feature).
elif contrast == 4:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    for i, col in enumerate(['color$','shape$','tri$','pos_[r,c]','size$']):
        features[f'x{2*i+1}'] = np.where(features.filter(regex=col) == 1, 1, 0).sum(axis=1)
        features[f'x{2*i+2}'] = np.where(features.filter(regex=col) == 2, 1, 0).sum(axis=1)
    
## Contrast 5: number of total rules (by type & feature) + distractor.
elif contrast == 5:
    
    ## Define intercept.
    features['x0'] = 1
    
    ## Define rule-based regressors.
    for i, col in enumerate(['color$','shape$','tri$','pos_[r,c]','size$']):
        features[f'x{2*i+1}'] = np.where(features.filter(regex=col) == 1, 1, 0).sum(axis=1)
        features[f'x{2*i+2}'] = np.where(features.filter(regex=col) == 2, 1, 0).sum(axis=1)
        
    ## Define distractor-based regressors.
    features['x11'] = np.where(features.distractor == 'md', 1, 0) 
    
## Contrast 6: number of total rules (by type & feature) + distractor + perceptual elements.
elif contrast == 6:
    
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
    
    raise ValueError(f'contrast type "{contrast}" not available.')
    
## Standardize regressors.
zscore = lambda x: (x - x.mean()) / x.std()
features[features.filter(regex='x[1-9]').columns] = features.filter(regex='x[1-9]').apply(zscore)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define response data.
Y = data.accuracy.values.astype(int)
    
## Define design matrix.
X = features.filter(regex='x[0-9]').values
    
## Define metadata.
N = len(Y)
M = len(X.T)
J = np.unique(data.subject, return_inverse=True)[-1] + 1
K = np.unique(data.item_id, return_inverse=True)[-1] + 1

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J, K=K, M=M, Y=Y, X=X)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models',f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}_m{contrast}')
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(f'{fout}_summary.tsv', sep='\t')

## Extract and save samples.
samples = StanFit.draws_pd()
samples.to_csv(f'{fout}.tsv.gz', sep='\t', index=False, compression='gzip')