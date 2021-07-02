functions {

    vector inv_logit_mars(vector x) {
        return 0.25 + 0.75 * inv(1. + exp(-x));
    }

}
data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  J[N];                // Subject-indicator per observation
    int<lower=1>  K[N];                // Item-indicator per observation
    
    // Data
    int  Y[N];                         // Response variable

}
parameters {

    // Subject abilities
    vector[max(J)]  theta;             // Subject abilities
    
    // Item parameters
    vector[max(K)]  alpha;             // Item difficulties    
    vector<lower=0>[max(K)]  beta;     // Item discriminations
    
    // Item variances
    real<lower=0>  sigma_alpha;
    real<lower=0>  sigma_beta;

}
model {
    
    // Construct predictor terms
    vector[N] mu = inv_logit_mars( beta[K] .* (theta[J] - alpha[K]) );
    
    // Likelihood
    target += bernoulli_lpmf( Y | mu );
    
    // Priors
    target += std_normal_lpdf(theta);
    target += normal_lpdf(alpha | 0, sigma_alpha);
    target += lognormal_lpdf(beta | 0, sigma_beta);
    target += student_t_lpdf(sigma_alpha | 3, 0, 2.5);
    target += student_t_lpdf(sigma_beta | 3, 0, 2.5);

}
generated quantities {

    // Posterior predictive check
    vector[max(K)] dLL = rep_vector(0, max(K));
    
    {
    
    // Construct predictor terms
    vector[N] mu = inv_logit_mars( beta[K] .* (theta[J] - alpha[K]) );
    
    // Simulate responses
    int Y_hat[N] = bernoulli_rng(mu);
    
    // Posterior predictive check
    for (n in 1:N) {
        dLL[K[n]] += bernoulli_lpmf(Y_hat[n] | mu[n]) - bernoulli_lpmf(Y[n] | mu[n]);
    }
    
    }

}