data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    int<lower=1>  M[N];                // Type-indicator per observation
    
    // Response data
    int           Y[N];                // Response accuracy

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items
    int  NM = max(M);                  // Number of total versions

}
parameters {

    // Subject abilities
    vector[NJ]  theta;                 // Subject abilities
    
    // Item difficulties
    vector[NM]     mu_pr;              // Population-level effects
    matrix[NM,NK]  beta_pr;            // Standardized item-level effects
    
    // Item variances
    cholesky_factor_corr[NM] L;        // Cholesky factor of correlation matrix
    vector<lower=0>[NM] sigma;         // Item-level standard deviations
    
}
transformed parameters {

    real beta[NK,NM] = to_array_2d(transpose(rep_matrix(mu_pr, NK) 
                       + diag_pre_multiply(sigma, L) * beta_pr));
    
}
model {
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = inv_logit(theta[J[n]] - beta[K[n],M[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta);
    target += std_normal_lpdf(to_vector(beta_pr));
    target += normal_lpdf(mu_pr | 0, 2);
    target += student_t_lpdf(sigma | 3, 0, 1);
    target += lkj_corr_cholesky_lpdf(L | 1);
    
}
generated quantities {

    // Correlation matrix
    matrix[NM,NM] Corr = tcrossprod(L);

}