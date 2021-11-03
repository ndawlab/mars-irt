import os, sys
import numpy as np
from os.path import dirname
from pandas import read_csv, get_dummies
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

## Prepare intercept variable.
features['intercept'] = 1

## Prepare rules variable.
features['n_rules'] = np.where(features.filter(regex='f[1-3]'), 1, 0).sum(axis=1)

## Prepare distractor variable.
features['distractor'] = features['distractor'].replace({'md':0.5, 'pd':-0.5})

## Prepare RT regressor.
rt = data.groupby('item_id').rt.apply(lambda x: np.mean(np.log(x))).values
X = features[['intercept','n_features','n_rules','distractor']].values
b, _, _, _ = np.linalg.lstsq(X, rt, rcond=-1)
features['rt'] = zscore(rt - X @ b).round(6)

## Define item feature matrix.
X2 = features[['intercept','n_features','n_rules','distractor','rt']].copy()
X2.to_csv(os.path.join(ROOT_DIR, 'designs', f'X2.csv'), index=False)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Construct item family matrix.
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Define item family matrix.
X3 = get_dummies(features.item)
X3.to_csv(os.path.join(ROOT_DIR, 'designs', f'X3.csv'), index=False)
