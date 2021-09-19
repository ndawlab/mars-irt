functions {

    real dlt_lpmf(int y, vector mu) {
      vector[4] p = ones_vector(4);    // Preallocate space        
      p[2:] = inv_logit(-mu);          // Compute distractor response weights        
      p /= sum(p);                     // Normalize weights        
      return log(p[y]);                // Return (log) probability of response
    }

}
data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M1;                  // Number of subject features
    int<lower=1>  M2;                  // Number of item features
    int<lower=1>  M3;                  // Number of distractor features
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int<lower=1>  Y[N];                // Response choice
    
    // Explanatory data
    matrix[max(J), M1]  X1;            // Subject feature matrix
    matrix[max(K), M2]  X2;            // Item feature matrix
    matrix[max(K), M3]  X3;            // Distractor feature matrix

}
transformed data {

    int  NJ = max(J);                  // Number of total subjects
    int  NK = max(K);                  // Number of total items

}
parameters {

    // Subject abilities
    vector[M1]  theta_mu;              // Population-level effects
    vector[NJ]  theta_pr;              // Standardized subject-level effects
    
    // Item difficulties
    vector[M2+1]  beta_mu;             // Population-level effects
    matrix[NK,3]  beta_pr;             // Standardized item-level effects
    
    // Item variances
    vector<lower=0>[1] sigma;          // Item-level standard deviations
    
}
transformed parameters {

    // Construct subject-level abilities
    vector[NJ] theta = X1 * theta_mu + theta_pr;
    
    // Construct item-level difficulties
    matrix[M3,NK] beta = transpose(
        rep_matrix(X2 * beta_mu[:M2], M3) + 
        X3 * beta_mu[M2+1] + 
        sigma[1] * beta_pr
    );
    
}
model {
    
    // Compute log-likelihood
    vector[N] LL;
    for (n in 1:N) {
        LL[n] = dlt_lpmf(Y[n] | theta[J[n]] - beta[,K[n]]);
    }
    
    // Accuracy likelihood
    target += sum(LL);
    
    // Priors
    target += std_normal_lpdf(theta_pr);
    target += std_normal_lpdf(to_vector(beta_pr));
    target += std_normal_lpdf(theta_mu);
    target += normal_lpdf(beta_mu | 0, 2.5);
    target += student_t_lpdf(sigma | 3, 0, 1);

}
