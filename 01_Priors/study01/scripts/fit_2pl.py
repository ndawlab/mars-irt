import os
import numpy as np
from os.path import dirname
from pandas import read_csv
from cmdstanpy import CmdStanModel
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = '2pl'

## Sampling parameters.
iter_warmup   = 2000
iter_sampling = 1000
chains = 4
thin = 1
parallel_chains = 4

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'study_02.csv'))

## Update columns.
data = data.rename(columns={'sub':'subject'})
data.columns = [s.lower() for s in data.columns]

## Format columns. 
data['item'] = data.puzzle.apply(lambda x: x.split('_')[0]).astype(int)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define metadata.
N = int(data.shape[0])

## Define data.
Y = data.accuracy.values.astype(int)

## Define mappings.
J = np.unique(data.subject, return_inverse=True)[-1] + 1
K = np.unique(data.item, return_inverse=True)[-1] + 1

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J, K=K, Y=Y)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models',f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, 
                           thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(os.path.join(ROOT_DIR, 'stan_results', f'2pl_summary.tsv'), sep='\t')

## Extract and save samples.
samples = StanFit.draws_pd()
samples.to_csv(os.path.join(ROOT_DIR, 'stan_results', f'2pl.tsv.gz'), sep='\t', index=False, compression='gzip')