import os, sys
import numpy as np
from os.path import dirname
from numba import njit
from pandas import read_csv
ROOT_DIR = dirname(dirname(dirname(os.path.realpath(__file__))))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = sys.argv[1]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'study02', 'data.csv'))

## Update columns.
data = data.rename(columns={'sub':'subject'})
data.columns = [s.lower() for s in data.columns]

## Format columns. 
data['item'] = data.puzzle.apply(lambda x: x.split('_')[0]).astype(int)

## Restrict to items with at least 50 data points.
data = data.groupby('item').filter(lambda x: x.subject.size >= 50)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define metadata.
N = int(data.shape[0])

## Define data.
Y = data.accuracy.values.astype(int)

## Define mappings.
J = np.unique(data.subject, return_inverse=True)[-1]
K = np.unique(data.item, return_inverse=True)[-1]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Extract parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load DataFrame.
StanFit = read_csv(os.path.join(ROOT_DIR, 'stan_results', 'study02', f'{stan_model}.tsv.gz'), sep='\t', compression='gzip')

## Extract parameters.
theta = StanFit.filter(regex='theta').values
beta  = StanFit.filter(regex='beta').values
alpha = StanFit.filter(regex='alpha').values
gamma = StanFit.filter(regex='gamma').values

## Handle nested parameters.
if stan_model == '2pl': gamma = np.zeros_like(beta)
elif stan_model == '3pl_fixed': gamma = 0.25 * np.ones_like(beta)
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Posterior predictive check.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
np.random.seed(47404)

@njit
def inv_logit(x):
    return 1. / (1 + np.exp(-x))

def waic(log_lik):
    lppd = np.log( np.exp(log_lik).mean(axis=0) )
    pwaic = np.var(log_lik, axis=0)
    return lppd - pwaic

## Compute linear predictor.
mu = gamma[:,K] + (1-gamma[:,K]) * inv_logit( alpha[:,K] * (theta[:,J] - beta[:,K]) )

## Simulate accuracy.
Y_hat = np.random.binomial(1, mu).mean(axis=0)

## Compute likelihood.
Y_pred = np.where(Y, mu, 1-mu).mean(axis=0)

## Compute WAIC.
WAIC = waic(np.log(np.where(Y, mu, 1-mu)))

## Store posterior predictive variables.
data['Y_hat'] = Y_hat
data['Y_pred'] = Y_pred
data['WAIC'] = WAIC

## Restrict DataFrame to columns of interest.
cols = ['subject','item','accuracy','Y_hat','Y_pred','WAIC']
data = data[cols]

## Save.
data.to_csv(os.path.join(ROOT_DIR, 'stan_results', 'study02', f'{stan_model}_ppc.tsv'), sep='\t', index=False)