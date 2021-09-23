data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M1;                  // Number of subject features
    int<lower=1>  M2;                  // Number of item features
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int<lower=0>  Y[N];                // Response choice
    
    // Explanatory data
    matrix[max(J), M1]  X1;            // Subject feature matrix
    matrix[max(K), M2]  X2;            // Item feature matrix

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items

}
parameters {

    // Subject abilities
    vector[M1]  theta_mu;              // Population-level effects
    vector[NJ]  theta_pr;              // Standardized subject-level effects
    
    // Item difficulties
    vector[M2]  beta_mu;               // Population-level effects
    vector[NK]  beta_pr;               // Standardized item-level effects
    
    // Item discriminations
    vector[M2]  alpha_mu;              // Population-level effects
    vector[NK]  alpha_pr;              // Standardized item-level effects
    
    // Item variances
    vector<lower=0>[2] sigma;          // Item-level standard deviations
    
}
transformed parameters {

    // Construct subject abilities
    vector[NJ] theta = X1 * theta_mu + theta_pr;
    
    // Construct item difficulties
    vector[NK] beta = X2 * beta_mu + sigma[1] * beta_pr;
    
    // Construct item discriminations
    vector[NK] alpha = exp(X2 * alpha_mu + sigma[2] * alpha_pr);
    
}
model {
    
    // Compute log-likelihood
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta_mu);
    target += std_normal_lpdf(theta_pr);
    target += normal_lpdf(beta_mu | 0, 2.5);
    target += std_normal_lpdf(beta_pr);
    target += std_normal_lpdf(alpha_mu);
    target += std_normal_lpdf(alpha_pr);
    target += student_t_lpdf(sigma | 3, 0, 1);

}
