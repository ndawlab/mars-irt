data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M1;                  // Number of subject features
    int<lower=1>  M2;                  // Number of item features
    int<lower=1>  M3;                  // Number of effort features
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int           Y[N];                // Response accuracy
    
    // Explanatory data
    matrix[max(J), M1]  X1;            // Subject feature matrix
    matrix[max(K), M2]  X2;            // Item feature matrix
    matrix[N, M3]       X3;            // Effort feature matrix

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items

}
parameters {

    // Subject abilities
    vector[M1]  theta_mu;              // Population-level effects
    vector[NJ]  theta_pr;              // Standardized subject-level effects
    
    // Item parameters
    vector[M2]    beta_mu;             // Population-level effects
    vector[M2]    alpha_mu;            // Population-level effects
    matrix[2,NK]  xi_pr;               // Standardized item-level effects
    
    // Item variances
    cholesky_factor_corr[2] L;         // Cholesky factor of correlation matrix
    vector<lower=0>[2] sigma;          // Item-level standard deviations
    
    // Effort-moderated variables
    vector[M3]  zeta_mu;               // Mixture coefficients
    
}
transformed parameters {

    vector[NJ] theta = X1 * theta_mu + theta_pr;
    vector[NK] beta;
    vector[NK] alpha;
    
    {
    matrix[NK,2] xi = transpose(diag_pre_multiply(sigma, L) * xi_pr);
    beta = X2 * beta_mu + xi[,1];
    alpha = exp(X2 * alpha_mu + xi[,2]);
    }
    
}
model {
    
    // Compute mixture weights
    vector[N] w = inv_logit(X3 * zeta);
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = 0.25 * w[n] + (1-w[n]) * inv_logit(alpha[K[n]] * theta[J[n]] - beta[K[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta_mu);
    target += std_normal_lpdf(theta_pr);
    target += normal_lpdf(beta_mu | 0, 2.5);
    target += std_normal_lpdf(alpha_mu);
    target += std_normal_lpdf(to_vector(xi_pr));
    target += student_t_lpdf(sigma | 3, 0, 1);
    target += lkj_corr_cholesky_lpdf(L | 1);
    target += normal_lpdf(zeta_mu | 0, 2.5);

}
