import os, sys
import numpy as np
from os.path import dirname
from numba import njit
from pandas import read_csv
from psis import psisloo
from tqdm import tqdm
from scipy.stats import norm
from scipy.special import logsumexp
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
np.random.seed(47404)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = sys.argv[1]

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'data.csv'))

## Apply rejections.
reject = read_csv(os.path.join(ROOT_DIR, 'data', 'reject.csv'))
data = data.loc[data.subject.isin(reject.query('reject==0').subject)]

## Re-index items.
data['item_id'] = data.apply(lambda x: '%0.2d' %x['item'] + '_' + x['distractor'], 1)

## Score missing data.
data['accuracy'] = data['accuracy'].fillna(0)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for Stan.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define metadata.
N = len(data)
J = np.unique(data.subject, return_inverse=True)[-1]
K = np.unique(data.item_id, return_inverse=True)[-1]

## Define response data.
Y = data.accuracy.values.astype(int)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Extract parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load DataFrame.
StanFit = read_csv(os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}.tsv.gz'), sep='\t', compression='gzip')

## Extract parameters.
theta = StanFit.filter(regex='theta\[').values
beta  = StanFit.filter(regex='beta\[').values
alpha = StanFit.filter(regex='alpha\[').values
if not np.any(alpha): alpha = np.ones_like(beta)

## Define guessing rate.
if '3pl' in stan_model: gamma = 0.25
else: gamma = 0.00
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Posterior predictive check.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Performing posterior predictive check.')

@njit
def inv_logit(x):
    return 1. / (1 + np.exp(-x))

## Define number of posterior samples.
n_iter = len(StanFit)

## Compute linear predictor.
mu = np.zeros((n_iter, N))
for n in tqdm(range(N)): mu[:,n] = alpha[:,K[n]] * theta[:,J[n]] - beta[:,K[n]]
    
## Compute p(correct | theta).
p = gamma + (1-gamma) * inv_logit(mu)

## Simulate accuracy.
y_hat = np.random.binomial(1, p).mean(axis=0)

## Compute likelihood.
y_pred = np.where(Y, p, 1-p).mean(axis=0)

## Compute conditional log-likelihood.
cll = np.log(np.where(Y, p, 1-p))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Compute marginal likelihood.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
## Citation: Merkle et al. (2019) [https://doi.org/10.1007/s11336-019-09679-0]
## Adapted from scripts:
##   - http://semtools.r-forge.r-project.org/mfrh_functions.R
##   - http://semtools.r-forge.r-project.org/replication-mfrh.R
##   - http://semtools.r-forge.r-project.org/rasch_edstan_modified.stan
print('Computing marginal likelihood.')

## Define standard quadrature points.
## source: [R] 'gauss.quad.prob' function {statmod}
std_quad = np.array([-8.717598e+00, -7.656038e+00, -6.767465e+00, -5.966015e+00, -5.218848e+00, 
                     -4.508930e+00, -3.825901e+00, -3.162776e+00, -2.514473e+00, -1.877058e+00,
                     -1.247312e+00, -6.224623e-01, -3.762359e-17, 6.224623e-01, 1.247312e+00,
                     1.877058e+00, 2.514473e+00, 3.162776e+00, 3.825901e+00, 4.508930e+00, 
                     5.218848e+00, 5.966015e+00, 6.767465e+00, 7.656038e+00, 8.717598e+00])
std_log_weights = np.log([1.530039e-17, 7.102103e-14, 3.791150e-11, 5.738024e-09, 3.530153e-07, 
                          1.067219e-05, 1.777669e-04, 1.757850e-03, 1.085676e-02, 4.337997e-02, 
                          1.148809e-01, 2.048510e-01, 2.481694e-01, 2.048510e-01, 1.148809e-01, 
                          4.337997e-02, 1.085676e-02, 1.757850e-03, 1.777669e-04, 1.067219e-05, 
                          3.530153e-07, 5.738024e-09, 3.791150e-11, 7.102103e-14, 1.530039e-17])

## Seperate out draws for residuals and their SD
resid = theta.mean(axis=0)
stddev = theta.std(axis=0)

## Preallocate space.
mll = np.zeros((n_iter, J.max()+1))

## Main loop.    
for j in tqdm(range(J.max()+1)):

    ## Set up adaptive quadrature using SD for residuals.
    sd_i = 1
    adapt_nodes = resid[j] + stddev[j] * std_quad
    log_weights = np.log(np.sqrt(2*np.pi)) + np.log(stddev[j]) + (std_quad**2 / 2) +\
                  norm(0,sd_i).logpdf(adapt_nodes) + std_log_weights

    ## Evaluate marginal log-likelihood with adaptive quadrature. 
    mu = alpha[:,K[J==j]] * theta[:,j,np.newaxis] - beta[:,K[J==j]]
    p = gamma + (1-gamma) * inv_logit(np.add.outer(adapt_nodes, mu))
    loglik_by_node = np.log(np.where(Y[J==j], p, 1-p)).sum(axis=-1)
    weighted_loglik_by_node = loglik_by_node.T + log_weights
    mll[:,j] = logsumexp(weighted_loglik_by_node, axis=1)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Model comparison.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Computing loo-cv.')

## Compute p_waic (effective number of parameters).
pwaic_u = cll.var(axis=0)
pwaic_c = mll.var(axis=0)

## Compute PSIS-LOO.
louo, louos, ku = psisloo(cll)    # leave one unit out (conditional likelihood)
loco, locos, kc = psisloo(mll)    # leave one cluster out (marginal likelihood)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Store and save data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
print('Saving data.')

## Store posterior predictive variables.
data['y_hat'] = y_hat
data['y_pred'] = y_pred
data['pwaic_u'] = pwaic_u
data['pwaic_c'] = pwaic_c[J]
data['louo'] = louos
data['loco'] = locos[J]
data['k_u'] = ku
data['k_c'] = kc[J]

## Restrict DataFrame to columns of interest.
cols = ['subject','trial','item_id','item','dimension','test_form','shape_set','distractor','choice','accuracy',
        'y_hat','y_pred','pwaic_u','pwaic_c','louo','loco','k_u','k_c']
data = data[cols]

## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}')

## Save.
data.to_csv(f'{fout}_ppc.csv', index=False)