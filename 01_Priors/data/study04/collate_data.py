import os, json
import numpy as np
from os.path import dirname, join
from pandas import DataFrame, concat
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
RAW_DIR = os.path.join(ROOT_DIR, 'raw')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Main loop.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Preallocate space.
METADATA = []
DATA = []

## Locate files.
files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith('json')])

for f in files:
    
    ## Define subject
    subject = f.replace('.json','')
    
    ## Load JSON.
    with open(os.path.join(RAW_DIR, f), 'r') as tmp:
        JSON = json.load(tmp)
        
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    ### Assemble metadata.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        
    ## Initialize dictionary.
    dd = dict(subject=subject, total_time=JSON[-1]['time_elapsed'] * 1e-3 / 60)
    
    ## Add metadata.
    demo, = [dd for dd in JSON if dd['trial_type'] == 'survey-demo']
    for k,v in demo['responses'].items(): dd[k] = v
        
    ## Append.
    METADATA.append(dd)
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
    ### Assemble MARS.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
        
    ## Extract MARS task.
    mars = [dd for dd in JSON if dd['trial_type'] == 'mars']
    mars = DataFrame(mars).query('item_set != "practice"')
    
    ## Reduce to columns of interest.
    cols = ['item_set','test_form','stimulus','distractor','accuracy','rt']
    mars = mars[cols]
    
    ## Format columns.
    mars['stimulus'] = mars.stimulus.apply(lambda x: x.split('_')[1]).astype(int)
    mars['rt'] = np.round(mars['rt'] * 1e-3, 3)
    mars.insert(0, 'subject', subject)
    mars.insert(1, 'trial', np.arange(mars.shape[0])+1)
    
    ## Append.
    DATA.append(mars)
    
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Save data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Concatenate data.
METADATA = DataFrame(METADATA).sort_values(['subject'])
DATA = concat(DATA).sort_values(['subject','trial'])

## Add dimensionality.
dimensionality = {
    1:2, 6:2, 19:2, 20:2,
    15:3, 10:3, 11:3, 18:3,
    16:4, 17:4, 12:4, 23:4,
    14:5, 26:5, 52:5, 59:5
}
DATA.insert(2, 'dimension', DATA.stimulus.replace(dimensionality))

## Save data.
METADATA.to_csv(os.path.join(DATA_DIR, 'metadata.csv'), index=False)
DATA.to_csv(os.path.join(DATA_DIR , 'data.csv'), index=False)
