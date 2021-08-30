import os, json
import numpy as np
from os.path import dirname, join
from pandas import DataFrame, concat, read_csv
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
    dd = dict(
        subject=subject, 
        screen_resolution=[dd for dd in JSON if dd['trial_type'] == 'mars'][-1]['screen_resolution'],
        total_time=np.round(JSON[-1]['time_elapsed'] * 1e-3, 3),
        image_load=JSON[0]['success']
    )
    
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
    mars['shape_set'] = mars.puzzle.apply(lambda x: x.split('/')[-1].replace('.jpeg','')[-1])
    
    ## Reduce to columns of interest.
    cols = ['item_set','test_form','shape_set','item','distractor','choice','accuracy','rt',
            'minimum_resolution','browser_interactions']
    mars = mars[cols]
    
    ## Format columns.
    mars['item_set'] = mars['item_set'].astype(int)
    mars['shape_set'] = mars['shape_set'].astype(int)
    mars['test_form'] = mars['test_form'].astype(int)
    mars['item'] = mars['item'].astype(int)
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
dimension = read_csv(os.path.join(DATA_DIR, 'dimensionality.csv'))
dimension = dimension.rename(columns={'Item':'item','Dimensionality Score':'dimension'})
DATA = DATA.merge(dimension, on='item').sort_values(['subject','trial']).reset_index(drop=True)
DATA = DATA[['subject','trial','item_set','item','dimension','test_form','shape_set','distractor','choice',
             'accuracy','rt','minimum_resolution','browser_interactions']]
   
## Insert item id.
f = lambda x: '_'.join(['%0.2d' %x[col] if col=='item' else str(x[col]) for col in ['item','distractor','shape_set']])
DATA.insert(3, 'item_id', DATA.apply(f, 1))
DATA['item_id'] = np.unique(DATA.item_id, return_inverse=True)[-1] + 1
    
## Save data.
METADATA.to_csv(os.path.join(DATA_DIR, 'metadata.tsv'), sep='\t', index=False)
DATA.to_csv(os.path.join(DATA_DIR , 'data.csv'), index=False)
