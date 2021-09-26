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
    
    // Item discriminations
    vector[NK]  alpha_pr;              // Standardized item-level effects
    
}
transformed parameters {

    // Construct item discriminations
    // vector[NK] alpha = exp(alpha_pr);
    vector[NK] alpha = Phi_approx(alpha_pr) * 2;
    
}
model {
    
    // Compute log-likelihood
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = 0.25 + (1-0.25) * inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta);
    target += normal_lpdf(beta | 0, 2.5);
    target += normal_lpdf(alpha_pr | 0, 0.5);

}
