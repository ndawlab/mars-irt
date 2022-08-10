data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M1;                  // Number of subject features
    int<lower=1>  M2;                  // Number of item features
    int<lower=1>  M3;                  // Number of item families
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int<lower=0>  Y[N];                // Response accuracy
    
    // Explanatory data
    matrix[max(J), M1]  X1;            // Subject feature matrix
    matrix[max(K), M2]  X2;            // Item feature matrix
    matrix[max(K), M3]  X3;            // Item family matrix

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items
    
    real gamma = 0.25;                 // Guessing rate
    real c = -0.625;                   // Adjustment for guessing 

}
parameters {

    // Subject abilities
    vector[M1]  theta_mu;              // Population-level effects
    vector[NJ]  theta_pr;              // Standardized subject-level effects
    
    // Item difficulties
    vector[M2]  beta_mu;               // Population-level effects
    vector[M3]  beta_1_pr;             // Standardized level-1 effects
    vector[NK]  beta_2_pr;             // Standardized level-2 effects
    
    // Item discriminations
    vector[M2]  alpha_mu;              // Population-level effects
    vector[M3]  alpha_1_pr;            // Standardized level-1 effects

    // Item variances
    vector<lower=0>[3] sigma;          // Standard deviations
    
}
transformed parameters {

    // Compute partial correlations
    vector[M1] rho = tanh(theta_mu) / sqrt(M1);

    // Construct subject abilities
    vector[NJ] theta = X1 * rho + sqrt(1 - sum(square(rho))) * theta_pr;
    
    // Construct item difficulties
    vector[NK] beta = (X2 * beta_mu) + (sigma[1] * X3 * beta_1_pr) + (sigma[2] * beta_2_pr);
    
    // Construct item discriminations
    vector[NK] alpha = Phi_approx(c + (X2 * alpha_mu) + (sigma[3] * X3 * alpha_1_pr)) * 5;
    
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
    target += std_normal_lpdf(beta_mu);
    target += std_normal_lpdf(beta_1_pr);
    target += std_normal_lpdf(beta_2_pr);
    target += std_normal_lpdf(alpha_mu);
    target += std_normal_lpdf(alpha_1_pr);
    target += student_t_lpdf(sigma | 3, 0, 1);

}
