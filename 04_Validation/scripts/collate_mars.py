import os, json
import numpy as np
from os.path import dirname, join
from pandas import DataFrame, concat, read_csv
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
RAW_DIR = os.path.join(ROOT_DIR, 'raw')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble MARS data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Locate files.
files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith('mars.json')])

## Main loop.
MARS = []
for f in files:
        
    ## Define subject
    subject = f.replace('_mars.json','')
    
    ## Load JSON.
    with open(os.path.join(RAW_DIR, f), 'r') as tmp:
        JSON = json.load(tmp)
        
    ## Extract MARS task.
    mars = [dd for dd in JSON if dd['trial_type'] == 'mars']
    mars = DataFrame(mars).query('item_set != "practice"').reset_index(drop=True)
    
    ## Reduce to columns of interest.
    cols = ['item_set','short_form','item','distractor','shape_set','choice','accuracy','rt',
            'all_loaded','minimum_resolution','browser_interactions']
    mars = mars[cols]
    
    ## Format columns.
    mars['rt'] = np.round(mars['rt'] * 1e-3, 3)
    mars['short_form'] = mars['short_form'].astype(int)
    mars['all_loaded'] = mars['all_loaded'].astype(int)
    mars.insert(0, 'subject', subject)
    mars.insert(1, 'trial', np.arange(mars.shape[0])+1)
    
    ## Append.
    MARS.append(mars)
    
## Concatenate and save data.
MARS = concat(MARS).sort_values(['subject','trial'])
MARS.to_csv(os.path.join(DATA_DIR, 'mars.csv'), index=False)