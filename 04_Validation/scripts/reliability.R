library('tidyr')
library('lavaan')
library('semTools')

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Reliability (MaRs-IB)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
mars = read.csv('../data/mars.csv')

## Apply rejections.
reject = read.csv('../data/reject.csv')
mars = mars[is.element(mars$subject, reject[reject$reject==0,'subject']),];

## Score missing data.
mars$accuracy = ifelse(is.na(mars$accuracy), 0, mars$accuracy);

## Define formula.
mod1f <- 'score =~ x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9 + x10 + x11 + x12'

for (i in 1:3) {
  
  ## Restrict data to current short form. Pivot DataFrame.
  sf = pivot_wider(mars[mars$short_form==i,], id_cols=subject, names_from=trial, 
                   names_prefix = 'x', values_from=accuracy, values_fill=0);
  
  ## Fit model.
  fit1f <- cfa(mod1f, data=sf, std.lv=T, ordered=T, estimator='WLSMV');
  
  ## Compute reliability.
  alpha = reliability(fit1f);
  
  ## Print to console.
  print(paste('mars-sf', i, ':', alpha[2]));
  
}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#
### Reliability (RPM)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

## Load data.
rpm = read.csv('../data/rpm.csv')

## Apply rejections.
reject = read.csv('../data/reject.csv')
rpm = rpm[is.element(rpm$subject, reject[reject$reject==0,'subject']),];

## Score missing data.
rpm$accuracy = ifelse(is.na(rpm$accuracy), 0, rpm$accuracy);

## Define formula.
mod1f <- 'score =~ x1 + x2 + x3 + x4 + x5 + x6 + x7 + x8 + x9'

## Restrict data to current short form. Pivot DataFrame.
sf = pivot_wider(rpm, id_cols=subject, names_from=trial, names_prefix = 'x', 
                 values_from=accuracy, values_fill=0);

## Fit model.
fit1f <- cfa(mod1f, data=sf, std.lv=T, ordered=T, estimator='WLSMV');

## Compute reliability.
alpha = reliability(fit1f);

## Print to console.
print(paste('rpm-sf:', alpha[2]));
