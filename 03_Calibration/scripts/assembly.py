import numpy as np

def inv_logit(x):
    """Inverse logit function."""
    return 1 / (1 + np.exp(-x))

def contingency(x,y):
    """Returns contingency table of two binary variables."""
    prop = np.zeros((2,2))
    prop[0,0] = np.mean(x * y)
    prop[0,1] = np.mean(x * (1-y))
    prop[1,0] = np.mean((1-x) * y)
    prop[1,1] = np.mean((1-x) * (1-y))
    return prop

def tetrachoric(prop):
    """Approximation of the tetrachoric correlation.
    
    Parameters
    ----------
    prop : array, shape (2,2)
        Contingency table of observed proportions.
    
    Returns
    -------
    tetrachoric : float
        Tetrachoric correlation.
        
    References
    ----------
    Bonett, D. G., & Price, R. M. (2005). Inferential methods for the tetrachoric 
    correlation coefficient. Journal of Educational and Behavioral Statistics, 
    30(2), 213-225.
    """
    
    ## Compute odds ratio.
    omega = (prop[0,0] * prop[1,1]) / (prop[0,1] * prop[1,0])
    
    ## Compute exponent.
    c = (1 - np.abs(prop[:,0].sum() - prop[0,:].sum())/5 -\
        np.square(0.5 - prop.min())) / 2
    
    return np.cos(np.pi / (1 + omega**c))