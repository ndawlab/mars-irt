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
stan_model = '2pl_fg'

## Model parameters.
contrast = 4

## Seed parameters.
seed = int(sys.argv[1])

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

## Define type indicator.
if contrast == 1:
    data['M'] = 0
elif contrast == 2:
    data['M'] = np.unique(data.distractor, return_inverse=True)[-1]
elif contrast == 3:
    data['M'] = np.unique(data.shape_set, return_inverse=True)[-1]
elif contrast == 4:
    data['M'] = data.apply(lambda x: str(x.distractor) + str(x.shape_set), axis=1)
    data['M'] = np.unique(data.M, return_inverse=True)[-1]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Simulate data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
np.random.seed(seed)
    
## Define useful functions.
def inv_logit(x):
    return 1. / (1 + np.exp(-x))
    
## Define metadata.
N = len(data)
J = np.unique(data.subject, return_inverse=True)[-1]
K = np.unique(data.item, return_inverse=True)[-1]
M = data.M.values.astype(int)
   
## Load item parameters.
params = np.load(os.path.join(ROOT_DIR, 'simulations', 'params.npz'))
beta = params['beta']
alpha = params['alpha']
    
## Simulate subject parameters.
theta = np.random.normal(0, 1, J.max() + 1)

## Compute linear predictor.
mu = np.zeros(N)
for n in range(N):
    mu[n] = 0.25 + (1-0.25) * inv_logit(alpha[K[n],M[n]] * theta[J[n]] - beta[K[n],M[n]])
    
## Simulate response data.
Y = np.random.binomial(1,mu).astype(int)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J+1, K=K+1, M=M+1, Y=Y)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models',f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Define fout.
fout = os.path.join(ROOT_DIR, 'simulations', f'{stan_model}_m{contrast}_s%0.3d' %seed)
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(f'{fout}_summary.tsv', sep='\t')