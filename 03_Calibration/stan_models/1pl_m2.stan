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
    vector[2]  mu_pr;
    
    // Random effects
    vector[NK]  beta_pr;
    
    // Item variances
    vector<lower=0>[1] sigma;          // Item-level standard deviations
    
}
transformed parameters {

    real  beta[NK, NM];
    
    // Construction block
    {
    
    beta[:,1] = to_array_1d((mu_pr[1] + sigma[1] * beta_pr) - mu_pr[2]);
    beta[:,2] = to_array_1d((mu_pr[1] + sigma[1] * beta_pr) + mu_pr[2]);
        
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
    target += normal_lpdf(mu_pr | 0, 2);
    target += student_t_lpdf(sigma | 3, 0, 1);
    
}