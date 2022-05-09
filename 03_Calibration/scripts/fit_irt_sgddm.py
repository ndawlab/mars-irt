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

## SGDDM paramers.
thin = 5

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
R_obs = np.zeros((n_samp, N))
R_hat = np.zeros((n_samp, N))

## Iterate over samples.
for n in tqdm(range(N)):
    
    ## Compute linear predictor.
    mu = mu = alpha[:,K[n]] * theta[:,J[n]] - beta[:,K[n]]
    
    ## Compute p(response).
    p = inv_logit(mu)
    
    ## Compute expectation.
    expected = p.mean()
    
    ## Simulate data.
    y_hat = np.random.binomial(1, p)
    
    ## Compute residuals (observed).
    R_obs[:,n] = Y[n] - expected
    
    ## Compute residuals (simulated).
    R_hat[:,n] = y_hat - expected
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Discrepancy measure: SGDDM.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Computing discrepancy (sgddm).')

@njit
def smbc(u, v):
    return (u @ v) / (np.sqrt(u @ u) * np.sqrt(v @ v))

## Define indices.
indices = np.tril_indices(data.item.nunique(), k=-1)
n_pairs = len(indices[0])

## Preallocate space.
summary = np.zeros((n_pairs, 3))
sgddm = np.zeros(3)

## Iteratively compute SGGDM.
for i in tqdm(range(0, n_samp, thin)):
    
    ## Compute SMBC (observed).
    data['r'] = R_obs[i]
    obs = data.pivot_table('r','subject','item').corr(smbc).values[indices]
    summary[:,0] += obs

    ## Compute SMBC (simulated).
    data['r'] = R_hat[i]
    hat = data.pivot_table('r','subject','item').corr(smbc).values[indices]
    summary[:,1] += hat
        
    ## Compute ppp-values.
    summary[:,2] += (obs < hat).astype(int)
        
    ## Compute SGDDM (observed). 
    obs = np.nanmean(np.abs(obs))
    sgddm[0] += obs
    
    ## Compute SGDDM (simulated). 
    hat = np.nanmean(np.abs(hat))
    sgddm[1] += hat
    
    ## Compute ppp-values.
    sgddm[2] += (obs < hat).astype(int)
    
## Normalize values.
summary /= n_samp
sgddm /= n_samp

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Store and save data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Convert to DataFrame.
df = DataFrame(np.row_stack([sgddm, summary]), columns=['obs', 'pred', 'pval']).round(6)
df.insert(0, 'k2', np.append(0, indices[1]))
df.insert(0, 'k1', np.append(0, indices[0]))
df = df.dropna()

## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}')

## Save.
df.to_csv(f'{fout}_sgddm.csv', index=False)