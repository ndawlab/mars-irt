data {

    // Metadata
    int<lower=1>  N;                   // Number of total observations
    int<lower=1>  M;                   // Number of total regressors
    
    // Data
    vector[N]    Y;                    // Dependent variable
    matrix[N,M]  X;                    // Design matrix
    
    // Hyperpriors
    real<lower=1> nu;                  // Degrees of freedom
   
}
parameters {

    // Regression coeffcients
    vector[M]  beta;
    
    // Residual variance
    real<lower=0> sigma;

}
model {

    // Likelihood
    target += student_t_lpdf(Y | nu, X * beta, sigma);

    // Priors
    target += normal_lpdf(beta | 0, 2.5);
    target += student_t_lpdf(sigma | 3, 0, 1);

}