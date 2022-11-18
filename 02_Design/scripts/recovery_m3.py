import os, sys
import numpy as np
from os.path import dirname
from cmdstanpy import CmdStanModel
from pandas import DataFrame, concat
from psis import psisloo
from scipy.stats import norm
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = sys.argv[1]
seed = int(sys.argv[2])

## Sampling parameters.
iter_warmup   = 3000
iter_sampling = 1000
chains = 4
thin = 1
parallel_chains = 4

## Simulation parameters.
n_subj = 1500               # number of total subjects
n_item = 384                # number of total items
n_test = 16                 # number of items per subject

## Item parameters.
beta_mu = 0.20
beta_sd = 1.55
alpha_mu = -0.62
alpha_sd = 0.17
gamma = 0.25

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
np.random.seed(seed)

## Define convenience functions.
zscore = lambda x: (x - np.mean(x)) / np.std(x)

## Define person attributes.
X1 = np.random.normal(0, 1, (n_subj,1))
X1 = zscore(X1)

## Define person ability.
r2 = [0.50]
theta = X1 @ np.sqrt(r2) + np.random.normal(0, np.sqrt(1 - np.sum(r2)), n_subj)
theta = zscore(theta)

## Define item attributes.
X2 = np.column_stack([    
    np.ones(n_item).reshape(-1, 1),                                    # Intercept
    np.repeat(np.random.normal(0, 1, (n_item // 6, 2)), 6, axis=0),    # Template-level attributes
    np.random.normal(0, 1, (n_item, 2))                                # Clone-level attributes
])
X2[:,1:] = np.apply_along_axis(zscore, 0, X2[:,1:])

## Generate item difficulty parameters.
r2 = [0.00, 0.20, 0.10, 0.20, 0.10]
beta = (
    X2 @ np.sqrt(r2) +\
    np.repeat(np.random.normal(0, np.sqrt((1 - np.sum(r2)) / 2), n_item // 6), 6) +\
    np.random.normal(0, np.sqrt((1 - np.sum(r2)) / 2), n_item)
)
beta = beta_mu + beta_sd * zscore(beta)

## Generate item discrimination parameters.
r2 = [0.00, 0.14, 0.07, 0.14, 0.07]
s = np.append(0, np.random.permutation([1,1,-1,-1]))
alpha = (
    X2 @ (np.sqrt(r2) * s) +\
    np.repeat(np.random.normal(0, np.sqrt((1 - np.sum(r2)) / 2), n_item // 6), 6) +\
    np.random.normal(0, np.sqrt((1 - np.sum(r2)) / 2), n_item)
)
alpha = norm.cdf(alpha_mu + alpha_sd * zscore(alpha)) * 5

## Sort items by difficulty.
ix = np.argsort(beta.reshape(-1, 6).mean(axis=1))
beta  = beta.reshape(-1, 6)[ix].flatten()
alpha = alpha.reshape(-1, 6)[ix].flatten()
X2 = X2.reshape(-1, 6, len(X2.T))[ix].reshape(n_item, -1)

## Generate template-to-clone mapping.
X3 = np.repeat(np.identity(n_item // 6), 6, axis=0)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Simulate data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def inv_logit(x):
    return 1 / (1 + np.exp(-x))

## Define metadata.
N = n_subj * n_test

## Define subject-to-trial mapping.
J = np.repeat(np.arange(n_subj), n_test)

## Define item-to-trial mapping.
K = []
a = np.arange(0, 64, 4); 
b = lambda: np.random.randint(0, 4, 16)
c = lambda: np.random.randint(0, 6, 16)
for _ in range(n_subj): K.append((a + b()) * 6 + c())
K = np.concatenate(K)

## Define feature metadata.
_, M1 = X1.shape
_, M2 = X2.shape
_, M3 = X3.shape

## Compute linear predictor.
mu = np.zeros(N)
for n in range(N): mu[n] = gamma + (1-gamma) * inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]])
    
## Simulate choice.
Y = np.random.binomial(1, mu)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J+1, K=K+1, M1=M1, M2=M2, M3=M3, Y=Y, X1=X1, X2=X2, X3=X3)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join(ROOT_DIR, 'stan_models', f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Extract parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load DataFrame.
samples = StanFit.draws_pd()

## Extract parameters.
theta_hat = samples.filter(regex='theta\[').values
beta_hat  = samples.filter(regex='beta\[').values
alpha_hat = samples.filter(regex='alpha\[').values
if not np.any(alpha_hat): alpha_hat = np.ones_like(beta_hat)
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Posterior predictive check.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Performing posterior predictive check.')

def inv_logit(x):
    return 1. / (1 + np.exp(-x))

## Define number of posterior samples.
n_iter = len(samples)

## Compute linear predictor.
mu = np.zeros((n_iter, N))
for n in range(N): mu[:,n] = alpha_hat[:,K[n]] * theta_hat[:,J[n]] - beta_hat[:,K[n]]
    
## Compute p(correct | theta).
p = gamma + (1-gamma) * inv_logit(mu)

## Compute conditional log-likelihood.
cll = np.log(np.where(Y, p, 1-p))

## Compute PSIS-LOO.
louo, _, _ = psisloo(cll)    # leave one unit out (conditional likelihood)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save samples.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')

## Extract summary and samples.
summary = StanFit.summary(percentiles=[2.5, 50, 97.5], sig_figs=6).T

## Define columns to save.
cols = np.concatenate([    
    summary.filter(regex='theta\[').columns,    # Person abilities
    summary.filter(regex='beta\[').columns,     # Item difficulties
    summary.filter(regex='alpha\[').columns,    # Item discriminations
    summary.filter(regex='_mu').columns,        # Item means
    summary.filter(regex='sigma\[').columns,    # Item variances
])

## Restrict to columns of interest.
summary = summary[cols].T

## Insert metadata.
params = np.concatenate([theta, beta, alpha]).round(6)
params = np.concatenate([params, np.repeat(np.nan, len(summary) - len(params))])
summary.insert(0, 'Latent', params)

## Insert LOO-CV.
summary.loc['loo'] = np.append(np.round(louo, 3), np.repeat(np.nan, len(summary.columns) - 1))

## Save.
fout = os.path.join(ROOT_DIR, 'stan_results', '%s_s%0.3d.csv' %(stan_model, seed))
summary.to_csv(fout)