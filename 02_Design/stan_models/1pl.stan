data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int<lower=0>  Y[N];                // Response choice

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items

}
parameters {

    // Subject abilities
    vector[NJ]  theta;                 // Standardized subject-level effects
    
    // Item difficulties
    vector[NK]  beta;                  // Standardized item-level effects
    
}
model {
    
    // Compute log-likelihood
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = inv_logit(theta[J[n]] - beta[K[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta);
    target += normal_lpdf(beta | 0, 2.5);

}
