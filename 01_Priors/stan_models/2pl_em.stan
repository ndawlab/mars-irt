data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M;                   // Number of EM predictors
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Response data
    int        Y[N];                   // Response accuracy

    // Design matrix
    matrix[N,M]  X;                    // Effort-modulated predictors

}
parameters {

    // Subject abilities
    vector[max(J)]  theta;             // Subject abilities
    
    // Item parameters
    vector[2]         xi_mu;           // Population-level effects
    matrix[2,max(K)]  xi_pr;           // Standardized item-level effects
    
    // Item variances
    cholesky_factor_corr[2] L;         // Cholesky factor of correlation matrix
    vector<lower=0>[2] sigma;          // Item-level standard deviations
    
    // Response time variables
    vector[M]  zeta;                   // Mixture coefficients
    
}
transformed parameters {

    vector[max(K)]  beta;              // Item difficulties
    vector[max(K)]  alpha;             // Item discriminations
    
    // Construction block
    {
    
    // Rotate random effects
    matrix[max(K),2] xi = transpose(diag_pre_multiply(sigma, L) * xi_pr);
    
    // Construct random effects
    beta = xi_mu[1] + xi[,1];
    alpha = exp(xi_mu[2] + xi[,2]);
    
    }
    
}
model {
    
    // Compute mixture weights
    vector[N] w = inv_logit( X * zeta );

    // Compute predictor terms
    vector[N] mu = 0.25 * w + (1-w) .* inv_logit( alpha[K] .* theta[J] - beta[K] );
    
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