import os
import numpy as np
from os.path import dirname
from pandas import DataFrame, read_csv
from statsmodels.api import Logit
from tqdm import tqdm
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Simulation parameters.
n_sim = 5000

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'data.csv'))

## Apply rejections.
reject = read_csv(os.path.join(ROOT_DIR, 'data', 'reject.csv'))
data = data.loc[data.subject.isin(reject.query('reject==0').subject)]

## Re-sort data.
data = data.sort_values('item').reset_index(drop=True)

## Score missing data.
data['accuracy'] = data['accuracy'].fillna(0)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble data for regression.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define useful functions.
def inv_logit(x):
    return 1 / (1 + np.exp(-x))

def zscore(x):
    return (x - np.mean(x)) / np.std(x)

## Define regressors.
data['x0'] = 1
data['x1'] = data.groupby('subject').accuracy.transform(np.sum)
data['x2'] = np.where(data.distractor == "md", 1, 0)
data['x3'] = np.where(data.shape_set == 2, 1, 0)
data['x4'] = np.where(data.shape_set == 3, 1, 0)

## Prepare data.
Y = data.accuracy.values
X = data.filter(regex='x[0-9]').values
K = data.item.values

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Compute observed effects.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Preallocate space.
params = np.zeros((np.unique(K).size, 9))

for i, k in enumerate(np.unique(K)):
        
    ## Restrict to current item.
    y = Y[K == k]
    x = X[K == k].copy()

    ## Normalize sum scores.
    x[:,1] = zscore(x[:,1] - y)

    ## Perform logistic regression.
    fit = Logit(y, x).fit(disp=0)

    ## Check convergence.
    if not fit.mle_retvals['converged']: 
        continue

    ## Compute coefficients.
    params[i,:5] = fit.params
        
    ## Compute contrast (distractor).
    f_test = fit.f_test([0,0,1,0,0])
    params[i,5] = f_test.fvalue.squeeze()
    params[i,7] = f_test.pvalue.squeeze()
    
    ## Compute contrast (shape set).
    f_test = fit.f_test([[0,0,0,1,0],[0,0,0,0,1]])
    params[i,6] = f_test.fvalue.squeeze()
    params[i,8] = f_test.pvalue.squeeze()
    
## Convert to DataFrame.
columns = ['b0','b1','b2','b3','b4','f1','f2','p1','p2']
params = DataFrame(params, columns=columns)
params.insert(0, 'item', np.unique(K))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Compute null effects.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
np.random.seed(47404)

## Preallocate space.
f_null = np.zeros((n_sim, 2))

for m in tqdm(range(n_sim)):
    
    ## Preallocate space.
    fvals = np.zeros((np.unique(K).size, 2))
    
    for i, k in enumerate(np.unique(K)):
        
        ## Restrict to current item.
        y = Y[K == k]
        x = X[K == k].copy()
        
        ## Normalize sum scores.
        x[:,1] = zscore(x[:,1] - y)
        
        ## Permute item feature labels.
        x[:,-3:] = x[np.random.permutation(np.arange(y.size)),-3:]
        
        ## Perform logistic regression.
        fit = Logit(y, x).fit(disp=0)
        
        ## Check convergence.
        if not fit.mle_retvals['converged']: 
            continue
            
        ## Compute test statistic.
        fvals[i,0] = fit.f_test([0,0,1,0,0]).fvalue.squeeze()
        fvals[i,1] = fit.f_test([[0,0,0,1,0],[0,0,0,0,1]]).fvalue.squeeze()
        
    ## Store maximum statistic.
    f_null[m] = fvals.max(axis=0)
    
## Compute family-wise error p-value.
params['fwe1'] = (np.sum(np.subtract.outer(params.f1.values, f_null[:,0]) < 0, axis=1) + 1) / (n_sim + 1)
params['fwe2'] = (np.sum(np.subtract.outer(params.f2.values, f_null[:,1]) < 0, axis=1) + 1) / (n_sim + 1)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save results.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define fout.
fout = os.path.join(ROOT_DIR, 'stan_results', 'dif.csv')

## Save summary.
params.round(6).to_csv(fout, index=False)