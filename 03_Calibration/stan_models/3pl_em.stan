data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    int<lower=1>  M[N];                // Distractor-indicator per observation
    
    // Response data
    int        Y[N];                   // Response accuracy

    // Design matrix
    matrix[N,3]  X;                    // Effort-moderated predictors

}
parameters {

    // Subject abilities
    vector[max(J)]  theta;             // Subject abilities
    
    // Item parameters
    vector[4]         xi_mu;           // Population-level effects
    matrix[4,max(K)]  xi_pr;           // Standardized item-level effects
    
    // Item variances
    cholesky_factor_corr[4] L;         // Cholesky factor of correlation matrix
    vector<lower=0>[4] sigma;          // Item-level standard deviations
    
    // Effort-moderated variables
    vector[3]  zeta;                   // Mixture coefficients
    
}
transformed parameters {

    real  beta[max(K),max(M)];         // Item difficulties
    real  alpha[max(K),max(M)];        // Item discriminations
    
    // Construction block
    {
    
    // Rotate random effects
    matrix[max(K),4] xi = transpose(rep_matrix(xi_mu, max(K)) + diag_pre_multiply(sigma, L) * xi_pr);
    
    // Construct random effects
    beta = to_array_2d(xi[,1:2]);
    alpha = to_array_2d(exp(xi[,3:4]));
    
    }
    
}
model {
    
    // Compute mixture weights
    vector[N] w = inv_logit( X * zeta );
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = 0.25 * w[n] + (1-w[n]) * inv_logit( alpha[K[n],M[n]] * theta[J[n]] - beta[K[n],M[n]] );
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf( Y | mu );
    
    // Priors
    target += std_normal_lpdf(theta);
    target += std_normal_lpdf(to_vector(xi_pr));
    target += normal_lpdf(xi_mu[1] | 0, 2);
    target += normal_lpdf(xi_mu[2] | 0, 1);
    target += student_t_lpdf(sigma | 3, 0, 1);
    target += lkj_corr_cholesky_lpdf(L | 2);
    target += normal_lpdf(zeta | 0, 2);
    
}
generated quantities {

    // Correlation matrix
    matrix[4,4] Corr = tcrossprod(L);

}