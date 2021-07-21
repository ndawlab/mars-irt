library(rstan)
options(mc.cores = parallel::detectCores())

## Load data.
data = read.csv('data.csv')

## Define item.
data$item = sub("_.*","",data$Puzzle)

## Define data (item accuracy).
Y = as.integer(data$Accuracy)

## Define mappings. 
J = as.integer(as.factor(data$sub))     # subject-to-observation mapping
K = as.integer(data$item)               # item-to-observation mapping

## Define metadata.
N = nrow(data)

## Assemble data for Stan.
irt_dat = list(N=N, J=J, K=K, Y=Y)

## Fit Stan Model.
fit <- stan(file = '2pl.stan', data = irt_dat,
            chains=4, iter=2000, warmup=1000, thin=1, seed=0)

## Extract samples.
samples = as.data.frame(fit)
write.csv(samples, '2pl_samples.csv', row.names=FALSE)

## Extract summary.
summary = summary(fit)$summary
write.csv(summary, '2pl_samples_summary.csv')
