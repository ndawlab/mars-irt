import os, sys
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from os.path import dirname
from pandas import DataFrame, read_csv
from scipy.stats import chi2
from tqdm import tqdm
sns.set_theme(style='white', context='notebook', font_scale=1.33)
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Define parameters.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## I/O parameters.
stan_model = sys.argv[1]

## Item fit parameters.
n_bins = 10

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
### Main loop.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
np.random.seed(47404)

## Define useful functions.
def inv_logit(x):
    return 1. / (1 + np.exp(-x))

## Define degrees of freedom.
if '1pl' in stan_model: df = n_bins - 1
else: df = n_bins - 2
    
## Define bins
bins = np.arange(100/n_bins,100,100/n_bins)

## Assert figure folder exists.
fdir = os.path.join(ROOT_DIR, 'stan_results', stan_model)
if not os.path.isdir(fdir): os.makedirs(fdir)

stats = []
for k in tqdm(np.unique(K)):    
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    ### Compute item fit statistics.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    ## Extract data.
    theta_j = theta[:,J[K==k]]
    y = Y[K==k]
    
    ## Define groupings.
    g = np.digitize(theta_j.mean(axis=0), np.percentile(theta_j.mean(axis=0), bins))
    
    ## Compute average ability.
    theta_j = np.column_stack([theta_j[:,g==i].mean(axis=1) for i in range(n_bins)])
    
    ## Compute expected correct. 
    mu = alpha[:,k] * theta_j.T - beta[:,k]
    p = gamma + (1-gamma) * inv_logit(mu.T)
    
    ## Compute observed proportions.
    _, N_s = np.unique(g, return_counts=True)
    N_1 = np.array([y[g==i].sum() for i in range(n_bins)])
    N_0 = N_s - N_1
    
    ## Compute Yen's Q1.     
    a = np.square(N_1 - N_s * p)
    b = N_s * p * (1-p)
    Q = np.sum(a / b, axis=1)
    
    ## Compute p-values.
    qval = np.mean(chi2(df).sf(Q) < 0.05)
    
    ## Store data.
    stats.append({'item': k+1, 'Q1': Q.mean(), 'p': qval})
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    ### Compute item response function.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
    ## Plot IRF.
    fig, ax = plt.subplots(1,1,figsize=(6,4))
    
    ## Sub-sample parameters.
    ix = np.random.choice(np.arange(beta.shape[0]), 200, replace=False)
    beta_s = beta[ix,k]; alpha_s = alpha[ix,k]
    
    ## Compute estimated IRF.
    x = np.linspace(-2.5,2.5,251)
    p = gamma + (1-gamma) * inv_logit(np.outer(x, alpha_s) - beta_s)
    mu = np.percentile(p, 50, axis=1)
    lb = np.percentile(p, 2.5, axis=1)
    ub = np.percentile(p, 97.5, axis=1)
    
    ## Plot IRF.
    ax.plot(x, mu, color='0.2', lw=2)
    ax.fill_between(x, lb, ub, color='0.5', alpha=0.2)
    ax.scatter(theta_j.mean(axis=0), N_1 / N_s, s=50)
    
    ## Add detail.
    ax.axhline(0.25, color='0.5', lw=0.5, linestyle='--')
    ax.annotate('p = %0.3f' %qval, xy=(0,0), xytext=(0.02,0.98), xycoords='axes fraction',
                va='top', ha='left', fontsize=14)
    ax.set(xlim=(-2.5, 2.5), xlabel=r'ability ($\theta$)', ylim=(-0.05,1.05), 
           ylabel='accuracy', title='item %0.3d' %(k+1))
    sns.despine()
    
    ## Save figure.
    plt.tight_layout()
    plt.savefig(os.path.join(fdir, 'item_%0.3d.png' %(k+1)))
    plt.close('all')
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save item fit statistics.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    
## Convert to DataFrame.
stats = DataFrame(stats)

## Save.
fout = os.path.join(ROOT_DIR, 'stan_results', f'{stan_model}_ifs.csv')
stats.to_csv(fout, index=False)