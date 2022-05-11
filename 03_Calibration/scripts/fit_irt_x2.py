import os, sys
import numpy as np
from os.path import dirname
from numba import njit
from pandas import DataFrame, read_csv
from itertools import combinations
from tqdm import tqdm
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
np.random.seed(47404)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = sys.argv[1]

## Define X2 parameters.
minlength = 17

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'data.csv'))

## Apply rejections.
reject = read_csv(os.path.join(ROOT_DIR, 'data', 'reject.csv'))
data = data.loc[data.subject.isin(reject.query('reject==0').subject)]

## Score missing data.
data['accuracy'] = data['accuracy'].fillna(0)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define metadata.
N = len(data)
J = np.unique(data.subject, return_inverse=True)[-1]
K = np.unique(data.item_id, return_inverse=True)[-1]

## Define response data.
Y = data.accuracy.values.astype(int)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Extract parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load DataFrame.
StanFit = read_csv(os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}.tsv.gz'), sep='\t', compression='gzip')
n_samp = len(StanFit)

## Extract parameters.
theta = StanFit.filter(regex='theta\[').values
beta  = StanFit.filter(regex='beta\[').values
alpha = StanFit.filter(regex='alpha\[').values
if not np.any(alpha): alpha = np.ones_like(beta)

## Define guessing rate.
if '1plg' or '3pl' in stan_model: gamma = 0.25
else: gamma = 0.00
   
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Posterior predictive check.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
np.random.seed(47404)

@njit
def inv_logit(x):
    return 1. / (1 + np.exp(-x))

## Preallocate space.
Y_hat = np.zeros((n_samp, N))

## Iterate over samples.
for n in tqdm(range(N)):
    
    ## Compute linear predictor.
    mu = alpha[:,K[n]] * theta[:,J[n]] - beta[:,K[n]]
    
    ## Compute p(response).
    p = gamma + (1-gamma) * inv_logit(mu)
    
    ## Compute expectation.
    expected = p.mean()
    
    ## Simulate data.
    Y_hat[:,n] = np.random.binomial(1, p)
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Discrepancy measure: observed scores.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Computing discrepancy (x2).')

## Compute observed scores.
S = data.groupby('subject').accuracy.sum()

## Compute observed counts.
NC = np.bincount(S, minlength=minlength) 

## Compute simulated scores.
S_hat = np.zeros((n_samp, J.max() + 1), dtype=int)
for j in np.unique(J): S_hat[:,j] = Y_hat[:,J==j].sum(axis=1)

## Compute simulated counts.
NCr = np.apply_along_axis(np.bincount, 1, S_hat, minlength=minlength)

## Convert to DataFrame.
NC = DataFrame(np.row_stack([NC, NCr]))

## Save.
NC.index = NC.index.rename('sample')
NC.to_csv(os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}_x2.csv'))