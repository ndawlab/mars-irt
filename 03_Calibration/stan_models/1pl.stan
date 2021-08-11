data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M;                   // Number of item predictors
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int        Y[N];                   // Response accuracy
    
    // Design matrix
    row_vector[M]  X[N];               // Item attributes

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items

}
parameters {

    // Subject abilities
    vector[NJ]  theta;                 // Subject abilities
    
    // Item difficulties
    vector[M]     mu_pr;               // Population-level effects
    matrix[M,NK]  beta_pr;             // Standardized item-level effects
    
    // Item variances
    cholesky_factor_corr[M] L;         // Cholesky factor of correlation matrix
    vector<lower=0>[M] sigma;          // Item-level standard deviations
    
}
transformed parameters {

    matrix[M,NK] beta = rep_matrix(mu_pr, NK) + diag_pre_multiply(sigma, L) * beta_pr;
    
}
model {
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = inv_logit( theta[J[n]] - X[n] * beta[,K[n]] );
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf( Y | mu );
    
    // Priors
    target += std_normal_lpdf(theta);
    target += std_normal_lpdf(to_vector(beta_pr));
    target += normal_lpdf(mu_pr | 0, 2);
    target += student_t_lpdf(sigma | 3, 0, 1);
    target += lkj_corr_cholesky_lpdf(L | 1);
    
}
generated quantities {

    // Correlation matrix
    matrix[M,M] Corr = tcrossprod(L);

}