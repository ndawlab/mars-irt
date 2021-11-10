import os, sys
import numpy as np
from os.path import dirname
from cmdstanpy import CmdStanModel
from pandas import DataFrame
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = 'tetrachoric'

## Simulation parameters.
n_samp = 1000
n_subj = 1500
n_item = 2

## Guessing parameters.
C = [0, 1/8, 1/6, 1/4]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Main loop.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
np.random.seed(47404)

## Define useful functions.
def inv_logit(x):
    return 1 / (1 + np.exp(-x))

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join(ROOT_DIR, 'stan_models',f'{stan_model}.stan'))

data = []    
for i in range(n_samp):

    ## Simulate parameters.
    theta = np.random.normal(0,1,n_subj)
    beta  = np.append(0, np.random.normal(0,1))
    alpha = np.ones_like(beta)
    
    ## Iterate over guessing rates.
    for c in C:

        ## Simulate behavior.
        p = c + (1-c) * inv_logit(alpha * np.subtract.outer(theta,beta))
        Y = np.random.binomial(1,p)
        
        ## Fit StanModel.
        dd = dict(J=n_subj, K=n_item, Y=Y)
        StanFit = StanModel.optimize(data=dd, seed=0)
        
        ## Extract tetrachoric correlation.
        rho, = StanFit.optimized_params_pd['S'].values

        ## Append information.
        data.append(dict(ix=i+1, c=c, beta=beta[-1], rho=rho))
        
## Convert to DataFrame.
data = DataFrame(data).round(6)

## Save.
data.to_csv(os.path.join(ROOT_DIR, 'stan_results', 'tetrachoric.csv'), index=False)