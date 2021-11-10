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

## Precompute residuals.
R = Y - p
R_hat = y_hat - p

## Clear memory.
del y_hat, p, theta, beta, alpha

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Unidimensionality check.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define all pairs of items.
K = np.unique(data.item, return_inverse=True)[-1]
all_pairs = list(combinations(np.sort(np.unique(K)), 2))

## Preallocate space.
gddm, gddm_hat = np.zeros((2,n_iter))

## Main loop.
info = []
c = 0

for k1, k2 in tqdm(all_pairs):
    
    ## Define indicies.
    match_1, = np.where(K==k1)                        # Find all subjects w/ item A
    match_2, = np.where(K==k2)                        # Find all subjects w/ item B
    ix1 = match_1[np.in1d(J[match_1], J[match_2])]    # Restrict to subjects w/ A+B
    ix2 = match_2[np.in1d(J[match_2], J[match_1])]    # Restrict to subjects w/ A+B
    N = ix1.size
    
    ## Error-catching.
    if N == 0: continue
        
    ## Compute MBC (observed).
    mbc = np.mean(R[:,ix1] * R[:,ix2], axis=1)
    gddm += np.abs(mbc)
        
    ## Compute MBC (predicted).
    mbc_hat = np.mean(R_hat[:,ix1] * R_hat[:,ix2], axis=1)
    gddm_hat += np.abs(mbc_hat)
        
    ## Store info.
    info.append(dict(A=k1, B=k2, mbc=np.mean(mbc), pval=np.mean(mbc > mbc_hat)))
        
    ## Increment counter.
    c += 1
    
## Compute and store generalized dimensionality discrepancy measure. 
gddm /= c; gddm_hat /= c
info.append(dict(A=-1, B=-1, mbc=np.mean(gddm), pval=np.mean(gddm > gddm_hat)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Store and save data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Convert to DataFrame.
info = DataFrame(info)

## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}')

## Save.
info.to_csv(f'{fout}_gddm.csv', index=False)