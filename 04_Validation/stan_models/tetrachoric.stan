functions {

    // Adapted from: https://github.com/stan-dev/stan/issues/2356
    real binormal_cdf(real z1, real z2, real rho) {
        if (z1 != 0 || z2 != 0) {
            real denom = fabs(rho) < 1.0 ? sqrt((1 + rho) * (1 - rho)) : not_a_number();
            real a1 = (z2 / z1 - rho) / denom;
            real a2 = (z1 / z2 - rho) / denom;
            real product = z1 * z2;
            real delta = product < 0 || (product == 0 && (z1 + z2) < 0);
            return 0.5 * (Phi(z1) + Phi(z2) - delta) - owens_t(z1, a1) - owens_t(z2, a2);
        }
        return 0.25 + asin(rho) / (2 * pi());
    }
  
    // Adapted from: https://discourse.mc-stan.org/t/bivariate-probit-in-stan/2025/7
    real biprobit_lpdf(vector y1, vector y2, real mu1, real mu2, real rho) {
    
        // Compute generated quantities
        int n = size(y1);
        vector[n] q1 = 2 * y1 - 1;
        vector[n] q2 = 2 * y2 - 1;
        vector[n] w1 = q1 * mu1;
        vector[n] w2 = q2 * mu2;
        vector[n] r12 = rho * q1 .* q2;

        // Compute log-likelihood
        real LL = 0;
        for (i in 1:n) {
            LL += log(binormal_cdf(w1[i], w2[i], r12[i]));
        }
        
        return LL;
    }
  
}
data {

    // Metadata
    int<lower=1>  J;                            // Number of subjects
    int<lower=1>  K;                            // Number of items
    
    // Data
    matrix<lower=0, upper=1>[J,K] Y;            // Response accuracy
    
}
transformed data {

    // Sample SD
    vector[K] sigma;
    for (k in 1:K) {
        sigma[k] = sqrt(mean(Y[,k]) * (1-mean(Y[,k])));
    }

}
parameters {

    // Item parameters
    vector[K]  mu;                              // Mean accuracy
    cholesky_factor_corr[K]  L;                 // Cholesky factor of correlation matrix
  
}
transformed parameters {

    corr_matrix[K] Omega = multiply_lower_tri_self_transpose(L);

}
model {

    // Likelihood
    for (k1 in 1:K) {
        for (k2 in (k1+1):K) {
            target += biprobit_lpdf(Y[,k1] | Y[,k2], mu[k1], mu[k2], Omega[k1,k2]);
        }
    }

    // Priors
    target += std_normal_lpdf(mu);
    target += lkj_corr_cholesky_lpdf(L | 1);
    
}
generated quantities {

    // Summability index
    real S;
    
    // Construction block
    {
    
    // Generated quantities
    real a = 0;
    real b = 0;
    
    // Compute pairwise correlations
    for (k1 in 1:K) {
        for (k2 in (k1+1):K) {
            a += Omega[k1,k2] * sigma[k1] * sigma[k2];
            b += sigma[k1] * sigma[k2];
        }
    }
    
    // Compute average
    S = a / b;
    
    }

}