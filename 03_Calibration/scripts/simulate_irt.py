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

## Seed parameters.
seed = int(sys.argv[2])

## Sampling parameters.
iter_warmup   = 2000
iter_sampling = 1000
chains = 4
thin = 1
parallel_chains = 4

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Simulate data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
np.random.seed(seed)
    
## Define useful functions.
def inv_logit(x):
    return 1. / (1 + np.exp(-x))
   
## Define metadata.
N = 1500 * 16
J = np.repeat(np.arange(1500),16)
K = []
for _ in range(1500):
    ix = np.arange(0,128,8) + np.random.choice(np.arange(8), 16, replace=True)
    K = np.concatenate([K, ix]).astype(int)
    
## Define parameters.
zscore = lambda x: (x - np.mean(x)) / np.std(x)
X1 = np.random.normal(0,0.33,1500)
theta = zscore(X1 + np.random.normal(0, 1, 1500))
X1 = X1.reshape(-1,1)
_, M1 = X1.shape

## 
beta = np.sort(np.random.normal(0,1,128))
alpha = inv_logit(1.7 * np.random.normal(0,0.4,128)) * 2
X2 = np.ones((128,1))
_, M2 = X2.shape 
    
## Compute linear predictor.
mu = np.zeros(N)
for n in range(N):
    mu[n] = 0.25 + (1-0.25) * inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]])
    
## Simulate response data.
Y = np.random.binomial(1,mu).astype(int)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J+1, K=K+1, M1=M1, M2=M2, X1=X1, X2=X2, Y=Y)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models', f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Define fout.
fout = os.path.join(ROOT_DIR, 'simulations', f'{stan_model}_s{seed}')
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(f'{fout}_summary.tsv', sep='\t')