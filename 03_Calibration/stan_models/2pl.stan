data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M;                   // Number of item predictors
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int           Y[N];                // Response accuracy
    
    // Design matrix
    row_vector[M] X[N];                // Item attributes

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items
    int  NM = M * 2;

}
parameters {

    // Subject abilities
    vector[NJ]  theta;                 // Subject abilities
    
    // Item difficulties
    vector[NM]    mu_pr;               // Population-level effects
    matrix[NM,NK] xi_pr;               // Standardized item-level effects
    
    // Item variances
    cholesky_factor_corr[NM] L;        // Cholesky factor of correlation matrix
    vector<lower=0>[NM] sigma;         // Item-level standard deviations
    
}
transformed parameters {

    matrix[M, NK]  beta;               // Item difficulties
    matrix[M, NK]  alpha;              // Item discriminations
    
    // Construction block
    {
    
    // Rotate random effects
    matrix[NM, NK] xi = rep_matrix(mu_pr, NK) + diag_pre_multiply(sigma, L) * xi_pr;
    
    // Construct random effects
    beta  = xi[:M];
    alpha = xi[M+1:];
    
    }
    
}
model {
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = inv_logit(exp(X[n] * alpha[,K[n]]) * theta[J[n]] - X[n] * beta[,K[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta);
    target += std_normal_lpdf(to_vector(xi_pr));
    target += normal_lpdf(mu_pr[:M] | 0, 2);
    target += normal_lpdf(mu_pr[M+1:] | 0, 1);
    target += student_t_lpdf(sigma | 3, 0, 1);
    target += lkj_corr_cholesky_lpdf(L | 1);
    
}
generated quantities {

    // Correlation matrix
    matrix[NM,NM] Corr = tcrossprod(L);

}