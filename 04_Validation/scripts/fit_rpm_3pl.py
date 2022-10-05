import os, sys
import numpy as np
from os.path import dirname
from pandas import read_csv, concat
from cmdstanpy import CmdStanModel
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = '3pl'

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
rpm = concat([
    read_csv(os.path.join(ROOT_DIR, 'data', 'shortform', 'rpm.csv')),
    read_csv(os.path.join(ROOT_DIR, 'data', 'longform', 'rpm.csv')),
])

## Apply rejections.
reject = concat([
    read_csv(os.path.join(ROOT_DIR, 'data', 'shortform', 'reject.csv')),
    read_csv(os.path.join(ROOT_DIR, 'data', 'longform', 'reject.csv'))
])
rpm  = rpm[rpm.subject.isin(reject.query('reject == 0').subject)].reset_index(drop=True)

## Score missing data.
rpm['accuracy'] = rpm['accuracy'].fillna(0)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define response data.
Y = rpm.accuracy.values.astype(int)

## Define metadata.
N = len(Y)
J = np.unique(rpm.subject, return_inverse=True)[-1] + 1
K = np.unique(rpm.stimulus, return_inverse=True)[-1] + 1

## Define item parameters.
gamma = np.concatenate([np.ones(2)/6, np.ones(7)/8])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J, K=K, Y=Y, gamma=gamma)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join(ROOT_DIR, 'stan_models', f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, 
                           thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}_rpm')
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(f'{fout}_summary.tsv', sep='\t')

## Extract and save samples.
samples = StanFit.draws_pd()
samples.to_csv(f'{fout}.tsv.gz', sep='\t', index=False, compression='gzip')