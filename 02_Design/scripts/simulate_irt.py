import os, sys
import numpy as np
from os.path import dirname
from cmdstanpy import CmdStanModel
from pandas import DataFrame, concat
from scipy.stats import norm
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = '2pl'
seed = int(sys.argv[1])

## Simulation parameters.
n_subj  = 800                # number of total subjects
n_item  = 60                 # number of total items
n_split = 4                  # number of item sets

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
    
## Define item order.
ix = np.arange(n_item).reshape(n_split, n_item // n_split, order='F')
K = np.zeros((n_subj, n_item // n_split), dtype=int)
for i in range(n_subj): 
    ix = np.apply_along_axis(np.random.permutation, 0, ix)
    K[i] = ix[0]
    
## Define metadata.
K = K.flatten()
J = np.repeat(np.arange(n_subj), n_item // n_split)
N = J.size

## Generate subject abilities.
theta = np.random.normal(0, 1, n_subj)

## Generate item parameters.
cov = [[1.5,0.0],[0.0,0.25]]
beta, alpha = np.random.multivariate_normal(np.zeros(2), cov, n_item).T
        
## Sort parameters.
alpha = np.exp(alpha[np.argsort(beta)])
beta  = beta[np.argsort(beta)]

## Generate data.
mu = inv_logit(alpha[K] * theta[J] - beta[K])
Y = np.random.binomial(1, mu).astype(int)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Fit Stan Model.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Assemble data.
dd = dict(N=N, J=J+1, K=K+1, Y=Y)

## Load StanModel
StanModel = CmdStanModel(stan_file=os.path.join('stan_models',f'{stan_model}.stan'))

## Fit Stan model.
StanFit = StanModel.sample(data=dd, chains=chains, iter_warmup=iter_warmup, iter_sampling=iter_sampling, 
                           thin=thin, parallel_chains=parallel_chains, seed=0, show_progress=True)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Select items.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define IRT functions.
def info_2pl(theta, beta, alpha):
    p = inv_logit(alpha * theta - beta)
    return alpha**2 * p * (1-p)

## Define templates.
x = np.linspace(-2,2,1001)
templates = np.row_stack([
    np.ones_like(x),
    norm(0,1).pdf(x)
])

## Extract samples.
samples = StanFit.draws_pd()
theta_hat = samples.filter(regex='theta').median().values
beta_hat  = samples.filter(regex='beta').median().values
alpha_hat = samples.filter(regex='alpha').median().values

## Compute item information.
info_true = np.zeros((n_item, x.size))
info_pred = info_true.copy()

for i in range(n_item): 
    info_true[i] = info_2pl(x, beta[i], alpha[i])
    info_pred[i] = info_2pl(x, beta_hat[i], alpha_hat[i])

## Greedy item selection (ground truth).
ground = np.zeros([templates.shape[0], 9], dtype=int)
for i, template in enumerate(templates):    
    for j in range(ground.shape[-1]):
        ix = np.setdiff1d(np.arange(n_item), ground[i,:j])
        tif = (info_true[ground[i,:j]].sum(axis=0) + info_true[ix]) @ template
        ground[i,j] = ix[np.argmax(tif)]
        
## Greedy item selection (chosen).
chosen = np.zeros([templates.shape[0], 9], dtype=int)
for i, template in enumerate(templates):    
    for j in range(chosen.shape[-1]):
        ix = np.setdiff1d(np.arange(n_item), chosen[i,:j])
        tif = (info_pred[chosen[i,:j]].sum(axis=0) + info_pred[ix]) @ template
        chosen[i,j] = ix[np.argmax(tif)]
        
## Greedy item selection (worst).
worst = np.zeros([templates.shape[0], 9], dtype=int)
for i, template in enumerate(templates):    
    for j in range(worst.shape[-1]):
        ix = np.setdiff1d(np.arange(n_item), worst[i,:j])
        tif = (info_pred[worst[i,:j]].sum(axis=0) + info_pred[ix]) @ template
        worst[i,j] = ix[np.argmin(tif)]
        
## Random item selection.
random = np.row_stack([
    np.random.choice(np.arange(n_item), 9, replace=False),
    np.random.choice(np.arange(n_item), 9, replace=False)
])

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', '%s_s%0.3d.npz' %(stan_model, seed))

## Save data.
np.savez_compressed(fout, theta=theta, theta_hat=theta_hat, beta=beta, beta_hat=beta_hat,
                    alpha=alpha, alpha_hat=alpha_hat, templates=templates, info=info_true,
                    ground=ground, chosen=chosen, random=random, worst=worst)