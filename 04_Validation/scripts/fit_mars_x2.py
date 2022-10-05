import os, sys
import numpy as np
from os.path import dirname
from pandas import read_csv
from numba import njit
from tqdm import tqdm
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = '3pl_fixed'
dataset = 'longform'

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
mars = read_csv(os.path.join(ROOT_DIR, 'data', dataset, 'mars.csv'))

## Apply rejections.
reject = read_csv(os.path.join(ROOT_DIR, 'data', dataset, 'reject.csv'))
mars  = mars[mars.subject.isin(reject.query('reject == 0').subject)].reset_index(drop=True)

## Score missing data.
mars['accuracy'] = mars['accuracy'].fillna(0)

## Load item parameters.
params = read_csv(os.path.join(ROOT_DIR, 'data', 'params.csv')).set_index('item_id')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define metadata.
N = len(mars)
J = np.unique(mars.subject, return_inverse=True)[-1]
K = np.unique(mars.item_id, return_inverse=True)[-1]

## Define response data.
Y = mars.accuracy.values.astype(int)

## Define item parameters.
beta  = params.beta[np.unique(mars.item_id)].values     # Item difficulty
alpha = params.alpha[np.unique(mars.item_id)].values    # Item discrimination
gamma = np.repeat(1/4., K.max()+1)                      # Item guessing

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Extract parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load DataFrame.
StanFit = read_csv(os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}_mars_{dataset}.tsv.gz'), sep='\t', compression='gzip')
n_samp = len(StanFit)

## Extract parameters.
theta = StanFit.filter(regex='theta').values

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
    mu = alpha[K[n]] * theta[:,J[n]] - beta[K[n]]
    
    ## Compute p(response).
    p = gamma[K[n]] + (1-gamma[K[n]]) * inv_logit(mu)

    ## Simulate data.
    Y_hat[:,n] = np.random.binomial(1, p)
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Discrepancy measure: observed scores.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Computing discrepancy (x2).')

## Define column.
if dataset == 'shortform': col = 'short_form'
elif dataset == 'longform': col = 'long_form'
else: raise ValueError('dataset "%s" not recognized.' %dataset)

## Compute observed scores.
S = mars.groupby('subject').accuracy.sum()

## Compute simulated scores.
S_hat = np.zeros((n_samp, J.max() + 1), dtype=int)
for j in np.unique(J): S_hat[:,j] = Y_hat[:,J==j].sum(axis=1)

for form in np.unique(mars[col]):

    ## Define index.
    ix = mars.groupby('subject')[col].mean().values == form
    
    ## Define minlength.
    minlength = mars.query('%s == %s' %(col, form)).item.nunique() + 1
    
    ## Compute observed counts.
    NC = np.bincount(S[ix], minlength=minlength) 

    ## Compute simulated counts.
    NCr = np.apply_along_axis(np.bincount, 1, S_hat[:,ix], minlength=minlength)
    ENC = NCr.mean(axis=0)
    
    ## Compute chi-square statistics.
    xi = np.sum(np.divide(np.square(NC - ENC), ENC, where=ENC > 0))
    xr = np.divide(np.square(NCr - ENC), ENC, where=ENC > 0).sum(axis=1)
    
    ## Compute ppp-value.
    pppv = (xi <= xr).mean()
    print('form %s: x2 = %0.3f (pppv = %0.3f)' %(form, xi, pppv))
   