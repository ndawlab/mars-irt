import os, json
import numpy as np
from os.path import dirname, join
from pandas import DataFrame, concat, read_csv
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
RAW_DIR = os.path.join(ROOT_DIR, 'raw')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble RPM data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Locate files.
files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith('rpm.json')])

## Main loop.
RPM = []
for f in files:
        
    ## Define subject
    subject = f.replace('_rpm.json','')
    
    ## Load JSON.
    with open(os.path.join(RAW_DIR, f), 'r') as tmp:
        JSON = json.load(tmp)
        
    ## Extract RPM task.
    rpm = [dd for dd in JSON if dd['trial_type'] == 'rpm']
    rpm = DataFrame(rpm)
    
    ## Reduce to columns of interest.
    cols = ['test_form','stimulus','correct','choice','accuracy','rt',
            'all_loaded','minimum_resolution']
    rpm = rpm[cols]
    
    ## Format columns.
    rpm['test_form'] = rpm['test_form'].replace({'a':0, 'b':1})
    try: rpm['stimulus'] = [s.split('/')[-1].replace('.png','') for s in rpm.stimulus]
    except: raise ValueError(f) 
    rpm['rt'] = np.round(rpm['rt'] * 1e-3, 3)
    rpm['all_loaded'] = rpm['all_loaded'].astype(int)
    rpm.insert(0, 'subject', subject)
    rpm.insert(1, 'trial', np.arange(rpm.shape[0])+1)
    
    ## Append.
    RPM.append(rpm)
    
## Concatenate and save data.
RPM = concat(RPM).sort_values(['subject','trial'])
RPM.to_csv(os.path.join(DATA_DIR, 'rpm.csv'), index=False)
