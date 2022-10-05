data {

    // Metadata
    int<lower=1>  N;                      // Number of total observations
    array[N] int<lower=1>  J;             // Subject-indicator per observation
    array[N] int<lower=1>  K;             // Item-indicator per observation
    
    // Response data
    array[N] int<lower=0, upper=1>  Y;    // Response accuracy
    
    // Item parameters
    vector[max(K)]  gamma;                // Item guessing

}
transformed data {

    int  NJ = max(J);                     // Number of total subjects
    int  NK = max(K);                     // Number of total items  
    real c = -0.841;                      // Adjustment for guessing 

}
parameters {

    // Subject abilities
    vector[NJ]   theta;                   // Standardized subject-level effects
    
    // Item parameters
    vector[NK]  beta;                     // Item difficulties
    vector[NK]  alpha_pr;                 // Item discriminations
    
}
transformed parameters {

    // Compute item discriminations
    vector[NK] alpha = Phi_approx(c + alpha_pr) * 5;

}
model {
    
    // Compute log-likelihood
    vector[N] mu;
    for (n in 1:N)
        mu[n] = gamma[K[n]] + (1-gamma[K[n]]) * inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]]);
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta);
    target += normal_lpdf(beta | 0, 2.5);
    target += std_normal_lpdf(alpha_pr);

}
