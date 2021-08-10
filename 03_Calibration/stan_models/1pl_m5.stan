data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    int<lower=1>  M[N];                // Version-indicator per observation
    
    // Response data
    int        Y[N];                   // Response accuracy

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items
    int  NM = max(M);                  // Number of total items

}
parameters {

    // Subject abilities
    vector[NJ]  theta;                 // Subject abilities
    
    // Fixed effects
    vector[3]  mu_pr;
    
    // Random effects
    vector[NK]  beta_pr;
    vector[NK]  beta_d_pr;
    vector[NK]  beta_t_pr;
    
    // Item variances
    vector<lower=0>[3] sigma;          // Item-level standard deviations
    
}
transformed parameters {

    real  beta[NK, NM];
    
    // Construction block
    {
    
    beta[:,1] = to_array_1d((mu_pr[1] + sigma[1] * beta_pr) - (mu_pr[2] + sigma[2] * beta_d_pr)
                  - (mu_pr[3] + sigma[3] * beta_t_pr));
    beta[:,2] = to_array_1d((mu_pr[1] + sigma[1] * beta_pr) - (mu_pr[2] + sigma[2] * beta_d_pr)
                  + (mu_pr[3] + sigma[3] * beta_t_pr));
    beta[:,3] = to_array_1d((mu_pr[1] + sigma[1] * beta_pr) + (mu_pr[2] + sigma[2] * beta_d_pr)
                  - (mu_pr[3] + sigma[3] * beta_t_pr));
    beta[:,4] = to_array_1d((mu_pr[1] + sigma[1] * beta_pr) + (mu_pr[2] + sigma[2] * beta_d_pr)
                  + (mu_pr[3] + sigma[3] * beta_t_pr));
        
    }

}
model {
    
    // Construct predictor terms
    vector[N] mu;
    for (n in 1:N) {
        mu[n] = inv_logit( theta[J[n]] - beta[K[n],M[n]] );
    }
    
    // Accuracy likelihood
    target += bernoulli_lpmf( Y | mu );
    
    // Priors
    target += std_normal_lpdf(theta);
    target += std_normal_lpdf(beta_pr);
    target += std_normal_lpdf(beta_d_pr);
    target += std_normal_lpdf(beta_t_pr);
    target += normal_lpdf(mu_pr | 0, 2);
    target += student_t_lpdf(sigma | 3, 0, 1);
    
}