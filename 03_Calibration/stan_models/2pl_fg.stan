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
    vector[NM]    beta_mu_pr;          // Population-level effects
    matrix[NM,NK] beta_pr;             // Standardized item-level effects
    
    // Item discriminations
    vector[NM]    alpha_mu_pr;         // Population-level effects
    matrix[NM,NK] alpha_pr;            // Standardized item-level effects
    
    // Item variances
    cholesky_factor_corr[NM] L[2];     // Cholesky factor of correlation matrix
    matrix<lower=0>[NM,2] sigma;       // Item-level standard deviations
    
}
transformed parameters {

    real beta[NK,NM]  = to_array_2d(transpose(rep_matrix(beta_mu_pr, NK) 
                        + diag_pre_multiply(sigma[:,1], L[1]) * beta_pr));
                        
    real alpha[NK,NM] = to_array_2d(exp(transpose(rep_matrix(alpha_mu_pr, NK) 
                        + diag_pre_multiply(sigma[:,2], L[2]) * alpha_pr)));
    
}
model {
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = 0.25 + (1-0.25) * inv_logit(alpha[K[n],M[n]] * theta[J[n]] - beta[K[n],M[n]]);
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu);
    
    // Priors
    target += std_normal_lpdf(theta);
    target += std_normal_lpdf(to_vector(beta_pr));
    target += std_normal_lpdf(to_vector(alpha_pr));
    target += normal_lpdf(beta_mu_pr | 0, 2);
    target += normal_lpdf(alpha_mu_pr | 0, 1);
    target += student_t_lpdf(to_vector(sigma) | 3, 0, 1);
    target += lkj_corr_cholesky_lpdf(L[1] | 1);
    target += lkj_corr_cholesky_lpdf(L[2] | 1);
    
}
generated quantities {

    // Correlation matrix
    matrix[NM,NM] Corr_b = multiply_lower_tri_self_transpose(L[1]);
    matrix[NM,NM] Corr_a = multiply_lower_tri_self_transpose(L[2]);

}