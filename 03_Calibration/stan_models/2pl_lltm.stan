data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M;                   // Number of item features
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int           Y[N];                // Response accuracy
    
    // Design matrix
    matrix[max(K), M]  X;              // Item feature matrix

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items

}
parameters {

    // Subject abilities
    vector[NJ]  theta;                 // Subject abilities
    
    // Item difficulties
    vector[M]   beta_mu_pr;            // Population-level effects
    vector[NK]  beta_pr;               // Standardized item-level effects
    
    // Item discriminations
    vector[M]   alpha_mu_pr;           // Population-level effects
    vector[NK]  alpha_pr;              // Standardized item-level effects
    
    // Item variances
    vector<lower=0>[2] sigma;          // Item-level standard deviations
    
}
transformed parameters {

    vector[NK] beta  = X * beta_mu_pr + sigma[1] * beta_pr;
    vector[NK] alpha = inv_logit(X * alpha_mu_pr + sigma[2] * alpha_pr) * 3;
    
}
model {
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta);
    target += std_normal_lpdf(beta_pr);
    target += std_normal_lpdf(alpha_pr);
    target += normal_lpdf(beta_mu_pr | 0, 2.5);
    target += normal_lpdf(alpha_mu_pr | 0, 2.5);
    target += student_t_lpdf(sigma | 3, 0, 1);
    
}
