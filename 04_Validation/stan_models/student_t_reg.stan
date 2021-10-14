data {

    // Metadata
    int  N;
    int  M;
    
    // Data
    vector[N]    Y;
    matrix[N,M]  X;
   
}
parameters {

    vector[M]  beta;
    real<lower=0> sigma;

}
model {

    // Likelihood
    target += student_t_lpdf(Y | 3, X * beta, sigma);

    // Priors
    target += normal_lpdf(beta | 0, 2.5);
    target += student_t_lpdf(sigma | 3, 0, 1);

}