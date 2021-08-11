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

## Sampling parameters.
iter_warmup   = 2500
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

## Define item version.
if ('m4' in stan_model) or ('m5' in stan_model) or ('m6' in stan_model):
    data['M'] = data.apply(lambda x: x.distractor + '_' + '%0.2d' %x.test_form, 1)
    data['M'] = np.unique(data['M'], return_inverse=True)[-1]
else:
    data['M'] = np.unique(data['distractor'], return_inverse=True)[-1]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define response data.
Y = data.accuracy.values.astype(int)

## Define metadata.
N = Y.size
J = np.unique(data.subject, return_inverse=True)[-1] + 1
K = np.unique(data.item, return_inverse=True)[-1] + 1
M = data['M'].values.astype(int) + 1

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J, K=K, M=M, Y=Y)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models',f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', stan_model)
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(f'{fout}_summary.tsv', sep='\t')

## Extract and save samples.
samples = StanFit.draws_pd()
samples.to_csv(f'{fout}.tsv.gz', sep='\t', index=False, compression='gzip')