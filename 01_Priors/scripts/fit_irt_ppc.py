import os, sys
import numpy as np
from os.path import dirname
from numba import njit
from pandas import read_csv
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = sys.argv[1]
study = int(sys.argv[2])

## Filter parameters.
p = 0.90

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'study%0.2d' %study, 'data.csv'))

## Set timeouts to incorrect.
data.accuracy = data.accuracy.fillna(0)
data.rt = data.rt.fillna(30)

## Filter easy trials.
data = data.groupby('item').filter(lambda x: x.accuracy.mean() < p)

## Prepare response times.
data['logrt'] = np.log(data.rt)
data['zrt'] = (data['logrt'] - data['logrt'].mean()) / data['logrt'].std()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define response data.
Y = data.accuracy.values.astype(int)

## Define effort predictors.
data['x1'] = np.ones_like(data.zrt)
data['x2'] = data.zrt
data['x3'] = np.square(data.zrt)
X = data.filter(regex='x[0-9]').values

## Define metadata.
N, M = X.shape
J = np.unique(data.subject, return_inverse=True)[-1]
K = np.unique(data.item, return_inverse=True)[-1]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Extract parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load DataFrame.
StanFit = read_csv(os.path.join(ROOT_DIR, 'stan_results', 'study%0.2d' %study, f'{stan_model}.tsv.gz'), sep='\t', compression='gzip')

## Extract parameters.
theta = StanFit.filter(regex='theta').values
beta  = StanFit.filter(regex='beta').values
alpha = StanFit.filter(regex='alpha').values
gamma = StanFit.filter(regex='gamma').values
zeta = StanFit.filter(regex='zeta').values

## Handle nested parameters.
if '2pl' in stan_model: gamma = np.zeros_like(beta)
elif 'fixed' in stan_model: gamma = 0.25 * np.ones_like(beta)
if not np.any(zeta): np.zeros((theta.shape[0], M))
    
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

## Compute mixture weights.
w = inv_logit(X @ zeta.T).T

## Compute linear predictor.
mu = 0.25 * w + (1-w) * (gamma[:,K] + (1-gamma[:,K]) * inv_logit(alpha[:,K] * theta[:,J] - beta[:,K]))

## Simulate accuracy.
Y_hat = np.random.binomial(1, mu).mean(axis=0)

## Compute likelihood.
Y_pred = np.where(Y, mu, 1-mu).mean(axis=0)

## Compute WAIC.
WAIC = waic(np.log(np.where(Y, mu, 1-mu)))

## Store posterior predictive variables.
data['w_hat'] = w.mean(axis=0)
data['Y_hat'] = Y_hat
data['Y_pred'] = Y_pred
data['WAIC'] = WAIC

## Restrict DataFrame to columns of interest.
cols = ['subject','trial','dimension','item','accuracy','rt','w_hat','Y_hat','Y_pred','WAIC']
data = data[cols]

## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', 'study%0.2d' %study)
if not os.path.isdir(fout): os.makedirs(fout)
fout = os.path.join(fout, stan_model)

## Save.
data.to_csv(f'{fout}_ppc.tsv', sep='\t', index=False)