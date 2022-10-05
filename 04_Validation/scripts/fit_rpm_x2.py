import os, sys
import numpy as np
from os.path import dirname
from pandas import read_csv, concat
from numba import njit
from tqdm import tqdm
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = '3pl'

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
rpm = concat([
    read_csv(os.path.join(ROOT_DIR, 'data', 'shortform', 'rpm.csv')),
    read_csv(os.path.join(ROOT_DIR, 'data', 'longform', 'rpm.csv')),
])

## Apply rejections.
reject = concat([
    read_csv(os.path.join(ROOT_DIR, 'data', 'shortform', 'reject.csv')),
    read_csv(os.path.join(ROOT_DIR, 'data', 'longform', 'reject.csv'))
])
rpm  = rpm[rpm.subject.isin(reject.query('reject == 0').subject)].reset_index(drop=True)

## Score missing data.
rpm['accuracy'] = rpm['accuracy'].fillna(0)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define response data.
Y = rpm.accuracy.values.astype(int)

## Define metadata.
N = len(Y)
J = np.unique(rpm.subject, return_inverse=True)[-1]
K = np.unique(rpm.stimulus, return_inverse=True)[-1]

## Define item parameters.
gamma = np.concatenate([np.ones(2)/6, np.ones(7)/8])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Extract parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load DataFrame.
StanFit = read_csv(os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}_rpm.tsv.gz'), sep='\t', compression='gzip')
n_samp = len(StanFit)

## Extract parameters.
theta = StanFit.filter(regex='theta').values
beta = StanFit.filter(regex='beta\[').values
alpha = StanFit.filter(regex='alpha\[').values

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
    p = gamma[K[n]] + (1-gamma[K[n]]) * inv_logit(mu)
    
    ## Simulate data.
    Y_hat[:,n] = np.random.binomial(1, p)
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Discrepancy measure: observed scores.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Computing discrepancy (x2).')

## Compute observed scores.
S = rpm.groupby('subject').accuracy.sum()

## Compute simulated scores.
S_hat = np.zeros((n_samp, J.max() + 1), dtype=int)
for j in np.unique(J): S_hat[:,j] = Y_hat[:,J==j].sum(axis=1)
    
## Define minlength.
minlength = rpm.stimulus.nunique() + 1

## Compute observed counts.
NC = np.bincount(S, minlength=minlength) 

## Compute simulated counts.
NCr = np.apply_along_axis(np.bincount, 1, S_hat, minlength=minlength)
ENC = NCr.mean(axis=0)

## Compute chi-square statistics.
xi = np.sum(np.divide(np.square(NC - ENC), ENC, where=ENC > 0))
xr = np.divide(np.square(NCr - ENC), ENC, where=ENC > 0).sum(axis=1)

## Compute ppp-value.
pppv = (xi <= xr).mean()
print('form: x2 = %0.3f (pppv = %0.3f)' %(xi, pppv))
