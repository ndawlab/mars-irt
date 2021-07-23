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
study = int(sys.argv[2])

## Sampling parameters.
iter_warmup   = 2000
iter_sampling = 1000
chains = 4
thin = 1
parallel_chains = 4

## Filter parameters.
p = 0.90

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'study%0.2d' %study, 'data.csv'))

## Set timeouts to incorrect.
data.accuracy = data.accuracy.fillna(0)
data.rt = data.rt.fillna(30)

## Filter easy trials.
data = data.groupby('item').filter(lambda x: x.accuracy.mean() < p)

## Prepare response times.
data['logrt'] = np.log(data.rt)
data['zrt'] = (data['logrt'] - data['logrt'].mean()) / data['logrt'].std()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define response data.
Y = data.accuracy.values.astype(int)

## Define effort predictors.
data['x1'] = np.ones_like(data.zrt)
data['x2'] = data.zrt
data['x3'] = np.square(data.zrt)
X = data.filter(regex='x[0-9]').values

## Define metadata.
N, M = X.shape
J = np.unique(data.subject, return_inverse=True)[-1] + 1
K = np.unique(data.item, return_inverse=True)[-1] + 1

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, M=M, J=J, K=K, Y=Y, X=X)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models',f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, 
                           thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', 'study%0.2d' %study)
if not os.path.isdir(fout): os.makedirs(fout)
fout = os.path.join(fout, stan_model)
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(f'{fout}_summary.tsv', sep='\t')

## Extract and save samples.
samples = StanFit.draws_pd()
samples.to_csv(f'{fout}.tsv.gz', sep='\t', index=False, compression='gzip')