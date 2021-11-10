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
# StanFit = StanFit.loc[::10]

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
print('Performing posterior predictive check.')

@njit
def inv_logit(x):
    return 1. / (1 + np.exp(-x))

## Define number of posterior samples.
n_iter = len(StanFit)

## Compute linear predictor.
mu = np.zeros((n_iter, N))
for n in tqdm(range(N)): mu[:,n] = alpha[:,K[n]] * theta[:,J[n]] - beta[:,K[n]]
    
## Compute p(correct | theta).
p = gamma + (1-gamma) * inv_logit(mu)

## Simulate accuracy.
y_hat = np.random.binomial(1, p)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Discrepancy measure.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Update item indices.
K = np.unique(data.item_id, return_inverse=True)[-1]

## Compute raw scores.
S = data.groupby('subject').accuracy.transform(np.sum).values

info = []
for k in tqdm(np.unique(K)):
    
    ## Initialize discrepancy metrics.
    sx, sx_hat = np.zeros((2,n_iter))
    
    ## Iterate raw scores.
    for s in np.unique(S):
        
        ## Define indices.
        ix, = np.where(np.logical_and(K==k, S==s))
        n = ix.size

        ## Error-catching.
        if not n: continue
        
        ## Compute Orlando & Thissen metric (observed).
        observed = np.mean(Y[ix])
        expected = np.mean(p[:,ix], axis=1)
        sx += n * np.square(observed - expected) / (expected * (1-expected))
        
        ## Compute Orlando & Thissen metric (predicted).
        observed = np.mean(y_hat[:,ix], axis=1)
        expected = np.mean(p[:,ix], axis=1)
        sx_hat += n * np.square(observed - expected) / (expected * (1-expected))
        
    ## Compute pval.
    pval = np.mean(sx > sx_hat)
        
    ## Append info.
    info.append(dict(item=k, discrepancy=np.mean(sx), pval=pval))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Store and save data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Convert to DataFrame.
info = DataFrame(info)

## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}')

## Save.
info.to_csv(f'{fout}_ifdm.csv', index=False)