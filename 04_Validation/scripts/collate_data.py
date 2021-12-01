import os, json
import numpy as np
from os.path import dirname, join
from pandas import DataFrame, concat, read_csv
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
RAW_DIR = os.path.join(ROOT_DIR, 'raw')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble metadata.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Locate files.
files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith('surveys.json')])

## Main loop.
METADATA = []
for f in files:
    
    ## Define subject
    subject = f.replace('_surveys.json','')
    
    ## Load JSON.
    with open(os.path.join(RAW_DIR, f), 'r') as tmp:
        JSON = json.load(tmp)
        
    ## Initialize dictionary.
    dd = dict(subject=subject)
    
    ## Add metadata.
    demo, = [dd for dd in JSON if dd['trial_type'] == 'survey-demo']
    for k,v in demo['responses'].items(): dd[k] = v
        
    ## Append.
    METADATA.append(dd)
    
## Concatenate and save data.
METADATA = DataFrame(METADATA).sort_values(['subject']).rename(columns={'gender-categorical':'gender'})
METADATA.to_csv(os.path.join(DATA_DIR, 'metadata.csv'), index=False)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble surveys.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Locate files.
files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith('surveys.json')])

## Main loop.
SURVEYS = []
for f in files:
    
    ## Define subject
    subject = f.replace('_surveys.json','')
    
    ## Load JSON.
    with open(os.path.join(RAW_DIR, f), 'r') as tmp:
        JSON = json.load(tmp)
        
    ## Initialize dictionary.
    dd = dict(subject=subject)
    
    ## Gather surveys.
    templates = [dd for dd in JSON if dd['trial_type'] == 'survey-template']
    
    for prefix in ['nfc10', 'pcf']:

        ## Extract survey.
        survey = [d for d in templates if prefix in d.get('survey', d['trial_type'])]
        if survey: survey, = survey
        else: continue

        ## Update dictionary.
        dd[f'{prefix}_rt'] = np.copy(np.round(survey['rt'] * 1e-3, 3))
        dd[f'{prefix}_radio'] = len(survey['radio_events'])
        dd[f'{prefix}_key'] = len(survey['key_events'])
        dd[f'{prefix}_mouse'] = len(survey['mouse_events'])
        dd[f'{prefix}_ipi'] = np.round(np.median(np.diff(survey['radio_events']) * 1e-3), 3)
        dd[f'{prefix}_infreq'] = survey['infrequency']
        dd[f'{prefix}_sl'] = np.round(survey['straightlining'], 3)
        dd[f'{prefix}_zz'] = np.round(survey['zigzagging'], 3)
        dd[f'{prefix}_bot'] = survey['honeypot']

        ## Reformat responses.
        survey = {f'{prefix}_{k.lower()}': int(survey['responses'][k]) for k in sorted(survey['responses'])}
        
        ## Update dictionary.
        dd.update(survey)
        
    ## Gather subjective numeracy scale.
    sns, = [d for d in JSON if 'sns' in d.get('survey', d['trial_type'])]
    sns = sns['response']
    sns = {('sns_q%0.2d' %(int(k[-1])+1)): int(sns[k]) for k in sorted(sns)}
    dd.update(sns)
    
    ## Append.
    SURVEYS.append(dd)
    
## Concatenate data.
SURVEYS = DataFrame(SURVEYS).sort_values(['subject'])

## Score SNS infrequency item.
SURVEYS['sns_infreq'] = np.where(SURVEYS['sns_q09'] == 0, 0, 1)

## Add summary stats.
SURVEYS.insert(1, 'infreq', SURVEYS.filter(regex='infreq').sum(axis=1))
SURVEYS.insert(2, 'straightlining', SURVEYS.filter(regex='sl').mean(axis=1).round(3))
SURVEYS.insert(3, 'zigzagging', SURVEYS.filter(regex='sl').mean(axis=1).round(3))
SURVEYS.insert(4, 'ipi', SURVEYS.filter(regex='ipi').mean(axis=1).round(3))
SURVEYS.insert(5, 'bot', SURVEYS.filter(regex='bot').sum(axis=1))

## Save data.
SURVEYS.to_csv(os.path.join(DATA_DIR, 'surveys.csv'), index=False)

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

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Assemble timing data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Locate files.
files = sorted([f for f in os.listdir(RAW_DIR) if f.endswith('surveys.json')])

## Main loop.
TIMING = []
for f in files:
    
    ## Define subject
    subject = f.replace('_surveys.json','')
        
    ## Initialize dictionary.
    dd = dict(subject=subject, mars_total=np.nan, mars_task=np.nan, mars_interactions=np.nan,
              rpm_total=np.nan, rpm_task=np.nan, rpm_interactions=np.nan)
    
    ## Process MARS data.
    fdat = os.path.join(RAW_DIR, f'{subject}_mars.json')
    
    if os.path.isfile(fdat):
        
        ## Load JSON.
        with open(fdat, 'r') as tmp:
            JSON = json.load(tmp)
            
        ## Extract total time.
        dd['mars_total'] = JSON[-1]['time_elapsed'] * 1e-3
        
        ## Extract task time.
        f = lambda d: d['rt'] if d['rt'] is not None else 3e4  
        dd['mars_task'] = sum([f(d) for d in JSON if 'short_form' in d]) * 1e-3
        
        ## Extract browser interactions.
        dd['mars_interactions'] = len(eval(JSON[-1]['interactions']))
        
    ## Process RPM data.
    fdat = os.path.join(RAW_DIR, f'{subject}_rpm.json')
    
    if os.path.isfile(fdat):
        
        ## Load JSON.
        with open(fdat, 'r') as tmp:
            JSON = json.load(tmp)
            
        ## Extract total time.
        dd['rpm_total'] = JSON[-1]['time_elapsed'] * 1e-3
        
        ## Extract task time.
        f = lambda d: d['rt'] if d['rt'] is not None else 3e4  
        dd['rpm_task'] = sum([f(d) for d in JSON if d['trial_type'] == 'rpm']) * 1e-3
        
        ## Extract browser interactions.
        dd['rpm_interactions'] = len(eval(JSON[-1]['interactions']))
        
    ## Append.
    TIMING.append(dd)
    
## Concatenate and save data.
TIMING = DataFrame(TIMING).sort_values(['subject'])
TIMING.to_csv(os.path.join(DATA_DIR, 'timing.csv'), index=False)
