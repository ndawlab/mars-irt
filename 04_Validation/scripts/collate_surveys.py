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