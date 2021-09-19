import os, sys
import numpy as np
from os.path import dirname
from pandas import read_csv
ROOT_DIR = dirname(dirname(os.path.realpath(__file__)))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Load and prepare data.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
data = read_csv(os.path.join(ROOT_DIR, 'data', 'data.csv'))
metadata = read_csv(os.path.join(ROOT_DIR, 'data', 'metadata.tsv'), sep='\t')

## Apply rejections.
reject = read_csv(os.path.join(ROOT_DIR, 'data', 'reject.csv'))
data = data.loc[data.subject.isin(reject.query('reject==0').subject)]
metadata = metadata.loc[metadata.subject.isin(reject.query('reject==0').subject)]

## Drop missing data.
data = data.dropna()

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Construct subject feature matrix.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Prepare gender variable.
gender = {'Male':-1,'Female':1,'Other':0,'Rather not say':0}
metadata['gender'] = metadata['gender-categorical'].replace(gender)

## Prepare age variable.
metadata['age'] = metadata.age.fillna(metadata.age.mean())

## Standardize RT regressors.
zscore = lambda x: (x - np.nanmean(x)) / np.nanstd(x)
data['y'] = zscore(np.log(data.rt))
data['x0'] = np.ones_like(data['y'])
data['x1'] = zscore(data.groupby('item_id').accuracy.transform(lambda x: 1 - np.mean(x)))

## Prepare RT variables.
regression = lambda df: np.linalg.lstsq(df[['x0','x1']], df['y'], rcond=-1)[0]
b0, b1 = np.row_stack(data.groupby('subject').apply(regression)).T
metadata['rt_0'] = b0
metadata['rt_1'] = b1

## Define subject feature matrix.
X1 = metadata[['age','gender','rt_0','rt_1']].copy()
X1.to_csv(os.path.join(ROOT_DIR, 'designs', f'X1.csv'), index=False)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Construct item feature matrix.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load features DataFrame.
features = read_csv(os.path.join(ROOT_DIR, 'designs', 'features.csv'))

## Reduce to item / distractor type. 
features = features.groupby(['item','distractor']).mean().reset_index()
features = features.sort_values(['item','distractor']).reset_index(drop=True)

## Prepare intercept variable.
features['intercept'] = 1

## Prepare rules variable.
features['n_rules'] = np.where(features.filter(regex='f[1-3]'), 1, 0).sum(axis=1)

## Prepare distractor variable.
features['distractor'] = features['distractor'].replace({'md':1, 'pd':0})

## Define item feature matrix.
X2 = features[['intercept','n_features','n_rules','distractor']].astype(int).copy()
X2.to_csv(os.path.join(ROOT_DIR, 'designs', f'X2.csv'), index=False)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Construct distractor feature matrix.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load distractors DataFrame.
distractors = read_csv(os.path.join(ROOT_DIR, 'designs', 'distractors.csv'))

## Reduce to item / distractor type. 
distractors = distractors.sort_values(['item','distractor']).reset_index(drop=True)
distractors = distractors.set_index(['item','distractor'])

## Prepare relative distractor variables.
distractors = distractors.apply(lambda x: x - x.min(), axis=1)

## Define distractor feature matrix.
X3 = distractors.copy()
X3.to_csv(os.path.join(ROOT_DIR, 'designs', f'X3.csv'), index=False)