import os, json
import numpy as np
from os.path import dirname
from pandas import DataFrame, concat
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
METADATA_DIR = os.path.join(ROOT_DIR, 'metadata')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Metadata directory.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Locate files.
files = sorted([f for f in os.listdir(METADATA_DIR) if f[0] in ['5','6']])

METADATA = []
for f in files:

    ## Load file.
    worker = f
    with open(os.path.join(METADATA_DIR, f), 'r') as f:
        for line in f.readlines():
            if 'subId' in line:
                METADATA.append( dict(workerId=worker, subId=line.strip().split('\t')[-1]) )

## Convert to DataFrame.
METADATA = DataFrame(METADATA)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Data directory.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Locate files.
files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('mars.json')])

MARS = []
for f in files:

    ## Load file.
    subject = f.replace('_mars.json','')
    with open(os.path.join(DATA_DIR, f), 'r') as f:
        JSON = json.load(f)

    ## Locate MARS trials.
    mars = DataFrame([dd for dd in JSON if dd['trial_type'] == 'mars'])
    mars = mars.query('item_set==3').fillna(0)

    ## Compute total points earned.
    score = mars.accuracy.sum()

    ## Store.
    MARS.append( dict(subId=subject, mars=score) )

## Convert to DataFrame.
MARS = DataFrame(MARS)

## Locate files.
files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('rpm.json')])

RPM = []
for f in files:

    ## Load file.
    subject = f.replace('_rpm.json','')
    with open(os.path.join(DATA_DIR, f), 'r') as f:
        JSON = json.load(f)

    ## Locate MARS trials.
    rpm = DataFrame([dd for dd in JSON if dd['trial_type'] == 'rpm'])
    rpm = rpm.fillna(0)

    ## Compute total points earned.
    score = rpm.accuracy.sum()

    ## Store.
    RPM.append( dict(subId=subject, rpm=score) )

## Convert to DataFrame.
RPM = DataFrame(RPM)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Compute bonus.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define maximum bonus.
completion_bonus = 0
max_bonus = 0.75

## Merge DataFrames.
BONUS = METADATA.merge(MARS, on='subId', how='inner').merge(RPM, on='subId', how='inner')
BONUS['score'] = (BONUS.mars + BONUS.rpm) / 21
BONUS['bonus'] = np.round(BONUS['score'] * max_bonus + completion_bonus, 2)
print(BONUS.bonus.sum())

## Save.
BONUS.to_csv(os.path.join(ROOT_DIR, 'payment', 'bonus.csv'), index=False, header=False, columns=('workerId','bonus'))
