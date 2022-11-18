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
stan_model = '3pl_fixed'
dataset = 'longform'

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
mars = read_csv(os.path.join(ROOT_DIR, 'data', dataset, 'mars.csv'))

## Apply rejections.
reject = read_csv(os.path.join(ROOT_DIR, 'data', dataset, 'reject.csv'))
mars  = mars[mars.subject.isin(reject.query('reject == 0').subject)].reset_index(drop=True)

## Score missing data.
mars['accuracy'] = mars['accuracy'].fillna(0)

## Load item parameters.
params = read_csv(os.path.join(ROOT_DIR, 'data', 'params.csv')).set_index('item_id')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define metadata.
N = len(mars)
J = np.unique(mars.subject, return_inverse=True)[-1] + 1
K = np.unique(mars.item_id, return_inverse=True)[-1] + 1

## Define response data.
Y = mars.accuracy.values.astype(int)

## Define item parameters.
beta  = params.beta[np.unique(mars.item_id)].values     # Item difficulty
alpha = params.alpha[np.unique(mars.item_id)].values    # Item discrimination
gamma = np.repeat(1/4., K.max())                        # Item guessing

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J, K=K, Y=Y, beta=beta, alpha=alpha, gamma=gamma)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join(ROOT_DIR, 'stan_models', f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}_mars_{dataset}')
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(f'{fout}_summary.tsv', sep='\t')

## Extract and save samples.
samples = StanFit.draws_pd()
samples.to_csv(f'{fout}.tsv.gz', sep='\t', index=False, compression='gzip')