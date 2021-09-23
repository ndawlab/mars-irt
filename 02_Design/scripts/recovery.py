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
stan_model = sys.argv[1]

## RNG parameters.
seed = int(sys.argv[2])

## Simulation parameters.
n_subj = 1500               # number of total subjects
n_item = 128                # number of total items
n_test = 16                 # number of items per subject

## Latent correlations.
rho = np.sqrt(0.5)

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

def zscore(x):
    return (x - np.mean(x)) / np.std(x)

## Define metadata.
N = n_subj * n_test

## Define subject-to-trial mapping.
J = np.repeat(np.arange(n_subj), n_test)

## Define item-to-trial mapping.
K = []
a = np.arange(0, n_item, n_item // n_test)
b = np.arange(n_item / n_test).astype(int)
for _ in range(n_subj): K.append(a + np.random.choice(b, n_test, replace=True))
K = np.concatenate(K)

## Define subject parameters.
cov = [[1,rho],[rho,1]]
theta, X1 = np.random.multivariate_normal(np.zeros(2), cov, n_subj).T
X1 = zscore(X1).reshape(-1,1)
_, M1 = X1.shape

## Define item parameters.
cov = [[1,0,rho],[0,0.25,0],[rho,0,1]]
beta, alpha, X2 = np.random.multivariate_normal(np.zeros(3), cov, n_item).T
X2 = np.column_stack([np.ones_like(X2), zscore(X2[np.argsort(beta)])])
beta = beta[np.argsort(beta)]
alpha = np.exp(alpha)
_, M2 = X2.shape

## Compute linear predictor.
mu = np.zeros(N)
for n in range(N): mu[n] = inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]])
    
## Simulate choice.
Y = np.random.binomial(1, mu)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, M1=M1, M2=M2, J=J+1, K=K+1, Y=Y, X1=X1, X2=X2)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join(ROOT_DIR, 'stan_models', f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')
    
## Extract samples.
samples = StanFit.draws_pd()
theta_hat = samples.filter(regex='theta\[').median().values
theta_sd  = samples.filter(regex='theta\[').std().values
beta_hat  = samples.filter(regex='beta\[').median().values
beta_sd   = samples.filter(regex='beta\[').std().values
alpha_hat = samples.filter(regex='alpha\[').median().values
alpha_sd  = samples.filter(regex='alpha\[').std().values

## Convert to DataFrame.
df = DataFrame(dict(
    seed = np.repeat(seed, n_subj + 2 * n_item),
    param = np.concatenate([np.repeat('theta',n_subj),np.repeat('beta',n_item),np.repeat('alpha',n_item)]),
    trial = np.concatenate([np.arange(n_subj),np.arange(n_item),np.arange(n_item)])+1, 
    latent = np.concatenate([theta, beta, alpha]).round(6),
    predicted = np.concatenate([theta_hat, beta_hat, alpha_hat]).round(6),
    stdev = np.concatenate([theta_sd, beta_sd, alpha_sd]).round(6)
))

## Save.
fout = os.path.join(ROOT_DIR, 'stan_results', '%s_s%0.3d.csv' %(stan_model, seed))
df.to_csv(fout, index=False)