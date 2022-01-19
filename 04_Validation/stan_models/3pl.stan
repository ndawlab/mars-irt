data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M;                   // Number of subject features
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int<lower=0>  Y[N];                // Response accuracy
    
    // Explanatory data
    matrix[max(J), M]  X;              // Subject feature matrix
    
    // Item parameters
    vector[max(K)]  beta;              // Item difficulties
    vector[max(K)]  alpha;             // Item discriminations

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items
    
    real gamma = 0.25;                 // Guessing rate

}
parameters {

    // Subject abilities
    vector[M]   theta_mu;              // Population-level effects
    vector[NJ]  theta_pr;              // Standardized subject-level effects
    
}
transformed parameters {

    // Compute partial correlations
    vector[M] rho = tanh(theta_mu) / sqrt(M);

    // Construct subject abilities
    vector[NJ] theta = X * rho + sqrt(1 - sum(square(rho))) * theta_pr;
    
}
model {
    
    // Compute log-likelihood
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = gamma + (1-gamma) * inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta_mu);
    target += std_normal_lpdf(theta_pr);

}
