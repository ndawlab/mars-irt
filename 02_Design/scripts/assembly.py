import os, sys
import numpy as np
from os.path import dirname
from scipy.stats import norm 
from pandas import DataFrame, read_csv
from mip import Model, OptimizationStatus, maximize, xsum, BINARY
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = sys.argv[1]
seed = int(sys.argv[2])

## Define assembly parameters.
n_item = 12                      # Test length.
dtol = 1e-1                      # TIF tolerance.
ptol = 1.0                       # Difficulty tolerance.

## Define 
pts = np.array([-1, -0.5, 0, 0.5, 1])
gamma = 0.25

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Main loop.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define convenience functions.
def inv_logit(arr):
    return 1 / (1 + np.exp(-arr))

## Load parameters.
summary = read_csv(os.path.join(ROOT_DIR, 'stan_results', '%s_s%0.3d.csv' %(stan_model, seed)), index_col=0)

## Define ability range.
theta = np.linspace(-3,3,1001)

## Define ability weights.
w = norm.pdf(theta)
w /= w.sum()

## Define item triplets.
triples = []
for i in range(0, 384, 3):
    triple = list(range(i,i+3))
    for j in range(3): triples.append(np.roll(triple, j).tolist())
n_triples = len(triples) 

## Preallocate space.
items = np.zeros((2, 3, n_item), dtype=int)

for n, var in enumerate(['Latent','Mean']):
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    ### Compute item functions.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    ## Extract item parameters.
    beta = summary.T.filter(regex='beta\[').T[var].values
    alpha = summary.T.filter(regex='alpha\[').T[var].values
    
    ## Compute item response function (full ability range).
    mu = np.outer(theta, alpha) - beta
    p = gamma + (1-gamma) * inv_logit(mu)
    P = w @ p
    
    ## Compute item response function (truncated ability range).
    mu = np.outer(pts, alpha) - beta
    p = gamma + (1-gamma) * inv_logit(mu)
    
    ## Compute item information function.
    I = np.transpose(np.square(alpha) * ((1-p) / p) * np.square((p - gamma) / (1 - gamma)))
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    ### Perform optimal test assembly.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    ## Initialize model.
    model = Model("assembly")

    ## Initialize binary variables.
    x = [model.add_var(var_type=BINARY) for i in range(n_triples)]

    ## Define model objective.
    model.objective = maximize(xsum(x[i] * I[ix].sum() for i, ix in enumerate(triples)))

    ## Constraint #1: maximum number of triples.
    model += xsum(x[i] for i in range(n_triples)) == n_item

    ## Constraint #2: one triplet per item family.
    for i in range(0, n_triples, 6): 
        model += xsum(x[i:i+6]) <= 1

    ## Constraint #3: minimize TIF differences.
    for k in range(I.shape[1]):
        model += xsum(x[i] * I[j,k] for i, (j,_,_) in enumerate(triples)) -\
                 xsum(x[i] * I[j,k] for i, (_,j,_) in enumerate(triples)) <= dtol
        model += xsum(x[i] * I[j,k] for i, (_,j,_) in enumerate(triples)) -\
                 xsum(x[i] * I[j,k] for i, (j,_,_) in enumerate(triples)) <= dtol
        model += xsum(x[i] * I[j,k] for i, (j,_,_) in enumerate(triples)) -\
                 xsum(x[i] * I[j,k] for i, (_,_,j) in enumerate(triples)) <= dtol
        model += xsum(x[i] * I[j,k] for i, (_,_,j) in enumerate(triples)) -\
                 xsum(x[i] * I[j,k] for i, (j,_,_) in enumerate(triples)) <= dtol

    ## Constraint #4: maximize form difficulty. 
    model += xsum(x[i] * P[j] for i, (j,_,_) in enumerate(triples)) / n_item <= ptol
    model += xsum(x[i] * P[j] for i, (_,j,_) in enumerate(triples)) / n_item <= ptol
    model += xsum(x[i] * P[j] for i, (_,_,j) in enumerate(triples)) / n_item <= ptol
    
    ## Perform optimization.
    status = model.optimize(max_seconds=300)
    assert status == OptimizationStatus.OPTIMAL
    
    ## Extract selected triplets.
    selected = [i for i in range(n_triples) if x[i].x]

    ## Construct test forms.
    items[n] = np.array([triples[i] for i in selected]).T
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Compute test information.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
from itertools import product

## (Re-)Extract item parameters. 
beta = summary.T.filter(regex='beta\[').T.Latent.values
alpha = summary.T.filter(regex='alpha\[').T.Latent.values

## Iterate over test forms.
info = []
for i, j in product(range(2), range(3)):
    
    ## Initialize dictionary.
    dd = {'model': stan_model, 'seed': seed, 'param': i, 'form': j+1}
    
    ## Compute TIF at points.
    mu = np.outer(pts, alpha[items[i,j]]) - beta[items[i,j]]
    p = gamma + (1-gamma) * inv_logit(mu)
    I = np.square(alpha[items[i,j]]) * ((1-p) / p) * np.square((p - gamma) / (1 - gamma))    
    TIF = I.sum(axis=1).round(6)
    
    ## Compute score reliability.
    mu = np.outer(theta, alpha[items[i,j]]) - beta[items[i,j]]
    p = gamma + (1-gamma) * inv_logit(mu)
    sigma_t = w @ np.square(p.sum(axis=1) - w @ p.sum(axis=1))    
    sigma_e = w @ np.sum(p * (1-p), axis=1)    
    rho = sigma_t / (sigma_t + sigma_e)
    
    ## Store. Append.
    dd.update({x: y for x, y in zip(pts, TIF)})
    dd['reliability'] = np.round(rho, 6)
    info.append(dd)
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save results.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
## Convert to DataFrame.
info = DataFrame(info)

## Format data.
info['param'] = info.param.replace({0: 'observed', 1: 'predicted'})

## Save data.
info.to_csv(os.path.join(ROOT_DIR, 'stan_results', '%s_s%0.3d_assembly.csv' %(stan_model, seed)), index=False)