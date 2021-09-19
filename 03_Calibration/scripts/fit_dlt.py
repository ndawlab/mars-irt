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
iter_warmup   = 2000
iter_sampling = 1000
chains = 1
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

## Re-index items.
data['item_id'] = data.apply(lambda x: '%0.2d' %x['item'] + '_' + x['distractor'], 1)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define metadata.
N = len(data)
J = np.unique(data.subject, return_inverse=True)[-1] + 1
K = np.unique(data.item_id, return_inverse=True)[-1] + 1

## Define response data.
Y = data.choice.values.astype(int) + 1

## Define convenience functions.
zscore = lambda x: (x - np.nanmean(x)) / np.nanstd(x)
    
## Define subject feature matrix.
X1 = read_csv(os.path.join(ROOT_DIR, 'designs', 'X1.csv'))
X1 = X1.apply(zscore, 0).values
_, M1 = X1.shape
    
## Define item feature matrix.
X2 = read_csv(os.path.join(ROOT_DIR, 'designs', 'X2.csv'))
X2 = X2.apply(zscore, 0).fillna(1).values
_, M2 = X2.shape

## Define distractor feature matrix.
X3 = read_csv(os.path.join(ROOT_DIR, 'designs', 'X3.csv'))
X3 = X3.values
_, M3 = X3.shape

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J, K=K, M1=M1, M2=M2, M3=M3, Y=Y, X1=X1, X2=X2, X3=X3)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models',f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}')
    
## Extract and save Stan summary.
summary = StanFit.summary()
summary.to_csv(f'{fout}_summary.tsv', sep='\t')

## Extract and save samples.
samples = StanFit.draws_pd()
samples.to_csv(f'{fout}.tsv.gz', sep='\t', index=False, compression='gzip')