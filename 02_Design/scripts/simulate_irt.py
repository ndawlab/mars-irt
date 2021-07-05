import os, sys
import numpy as np
from os.path import dirname
from cmdstanpy import CmdStanModel
from pandas import DataFrame, concat
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = '2pl'

## Simulation parameters.
fout = sys.argv[1]
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

def inv_logit(x):
    return 1 / (1 + np.exp(-x))

## Define task design.
design = np.atleast_2d(np.arange(15))
    
## Define metadata.
n_samp = 300
    
## Define mappings.
J, K = [], []
for i in np.arange(n_samp):
    J.append(np.repeat(i, design.shape[-1]))
    K.append(design[i % design.shape[0]])
J = np.concatenate(J); K = np.concatenate(K)
N = J.size
    
## Generate latent parameters.
theta = np.random.normal(0, 1, n_samp)
beta  = np.random.normal(0, 1, K.max()+1)
alpha = np.exp(np.random.normal(0, 0.33, K.max()+1))

## Generate data.
mu = inv_logit(alpha[K] * (theta[J] - beta[K]))
Y = np.random.binomial(1, mu).astype(int)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J+1, K=K+1, Y=Y)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models',f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Extract samples.
samples = StanFit.draws_pd()

## Construct DataFrame. 
data = concat([
    DataFrame(dict(
        param=np.repeat('theta',theta.size), 
        obs=theta, 
        pred=samples.filter(regex='theta').mean().values
    )),
    DataFrame(dict(
        param=np.repeat('beta',beta.size), 
        obs=beta, 
        pred=samples.filter(regex='beta').mean().values
    )),
    DataFrame(dict(
        param=np.repeat('alpha',alpha.size), 
        obs=alpha, 
        pred=samples.filter(regex='alpha').mean().values
    )),
])

## Append metadata.
data.insert(0, 'n_samp', J.max()+1)
data.insert(1, 'n_item', K.max()+1)
data.insert(2, 'seed', seed)

## Save.
data.to_csv(os.path.join('stan_results', f'%s_s%0.3d.csv' %(fout, seed)), index=False)