data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M1;                  // Number of item features
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int           Y[N];                // Response accuracy
    
    // Design matrix
    matrix[max(K), M1]  X1;            // Item feature matrix

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items

}
parameters {

    // Subject abilities
    vector[NJ]  theta;                 // Subject abilities
    
    // Item difficulties
    vector[M1]  beta_mu_pr;            // Population-level effects
    vector[NK]  beta_pr;               // Standardized item-level effects     
    
    // Item variances
    real<lower=0> sigma;               // Item-level standard deviations
    
}
transformed parameters {

    vector[NK] beta = X1 * beta_mu_pr + sigma * beta_pr;
    
}
model {
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = inv_logit(theta[J[n]] - beta[K[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta);
    target += std_normal_lpdf(beta_pr);
    target += normal_lpdf(beta_mu_pr | 0, 2.5);
    target += student_t_lpdf(sigma | 3, 0, 1);
    
}
