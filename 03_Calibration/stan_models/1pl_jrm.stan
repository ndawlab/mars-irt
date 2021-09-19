data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M1;
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int           Y[N];                // Response accuracy
    vector[N]     Z;                   // Response time
    
    // Explanatory data
    matrix[]

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items

}
parameters {

    // Subject parameters
    matrix[2,NJ]  theta_pr;            // Standardized subject-level effects     
    
    // Item parameters
    matrix[2,NK]  xi_pr;               // Standardized item-level effects     
    vector[2] xi_mu_pr;                // Population-level effects
    
    // Item variances
    cholesky_factor_corr[2] L_theta;   // Cholesky factor of correlation matrix
    cholesky_factor_corr[2] L_xi;      // Cholesky factor of correlation matrix
    vector<lower=0>[2] sigma;          // Item-level standard deviations
    real<lower=0> sigma_z;             // Response time standard deviation
    
}
transformed parameters {

    // Subject parameters
    vector[NJ]  theta_y;
    vector[NJ]  theta_z;

    // Item parameters
    vector[NK]  beta_y;
    vector[NK]  beta_z;
    
    {
    
    // Construct subject parameters
    matrix[NJ,2] theta = transpose(L_theta * theta_pr);
    theta_y = theta[,1];
    theta_z = theta[,2];
    
    // Construct item parameters
    matrix[NK,2] xi = transpose(rep_matrix(xi_mu_pr, NK) + diag_pre_multiply(sigma, L_xi) * xi_pr);
    beta_y = xi[,1];
    beta_z = xi[,2];
    
    }
    
}
model {
    
    // Preallocate space
    vector[N] mu_y;
    vector[N] mu_z;
    
    // Construct predictor terms
    for (n in 1:N) {
        mu_y[n] = inv_logit(theta_y[J[n]] - beta_y[K[n]]);
        mu_z[n] = theta_z[J[n]] - beta_z[K[n]];
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf(Y | mu_y);
    target += normal_lpdf(Z | mu_z, sigma_z);
    
    // Priors
    target += std_normal_lpdf(to_vector(theta_pr));
    target += std_normal_lpdf(to_vector(xi_pr));
    target += normal_lpdf(xi_mu_pr | 0, 2.5);
    target += lkj_corr_cholesky_lpdf(L_theta | 1);
    target += lkj_corr_cholesky_lpdf(L_xi | 1);
    target += student_t_lpdf(sigma | 3, 0, 1);
    target += student_t_lpdf(sigma_z | 3, 0, 1);

    
}
