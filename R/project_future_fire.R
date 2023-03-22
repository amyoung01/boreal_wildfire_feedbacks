#!/usr/bin/env Rscript

# Initialize workspace --------------------------------------------------------
set.seed(314159)

# -----------------------------------------------------------------------------
# TODO: how to read in config.yaml file into R --------------------------------
# -----------------------------------------------------------------------------
src <- c("era5", "EC-Earth3-Veg", "MPI-ESM1-2-HR", "MRI-ESM2-0", "CNRM-CM6-1-HR")

# Read in list of model files --------------------------------------------------
files <- list.files(path = "data/model_results",
                    pattern = "\\.RData$")

ecos_size <- "data/dataframes/ecoregion_size.csv"
ecos_size <- read.csv(ecos_size)

regression_forms <- read.csv("data/dataframes/regression_predictors.csv")

unique_ecos <- ecos_size$ecos

# No projected fire year may be larger than 6 times the max historical
max_frac <- 6

# Make projections of future area burned for each gcm --------------------------
for (mdl in src) {

    pred_vars_file <- list.files(path = "data/dataframes",
                                 pattern = sprintf("cffdrs-stats_%s.*", mdl),
                                 full.names = TRUE)
    pred_vars <- read.csv(pred_vars_file)
    pred_yrs <- unique(pred_vars$year)

    for (f in seq_along(files)) {

        # Load in Bayesian regression results
        file_i <- files[f]
        jags_results <- load(file.path("data/model_results", file_i))

        # Get metadata from file name
        file_name <- strsplit(file_i, "\\.")[[1]][1]
        file_parts <- strsplit(file_name, "_")[[1]]
        distr <- file_parts[2]
        sim <- file_parts[3]
        ecos <- as.numeric(file_parts[4])

        # Get specific predictor variable for given ecoregion
        mdl_form <- regression_forms$mdl[regression_forms$ecos == ecos]
        mdl_parts <- strsplit(mdl_form, " ")[[1]]
        isi_var <- mdl_parts[3]
        bui_var <- mdl_parts[5]

        pred_vars_i <- pred_vars[pred_vars$ecos == ecos, ]
        data <- data.frame(year = pred_vars_i$year,
                           bui = pred_vars_i[[bui_var]],
                           isi = pred_vars_i[[isi_var]])

        year <- jags_output$model$year
        aab <- jags_output$model$data()$aab
        w <- jags_output$model$data()$w
        S <- jags_output$model$data()$S

        sims <- jags_output$BUGSoutput$sims.list
        betas <- cbind(sims$beta0, sims$beta1, sims$beta2)

        aab_init <- sims$aab_init
        max_aab <- max_frac * max(aab)

        # Number of simulations
        N <- nrow(betas)

        export_mtx <- matrix(NA, nrow = N, ncol = length(pred_yrs))
        prior_aab <- matrix(NA, nrow = N, ncol = length(w))

        # Vector of shape parameter estimates (N x 1)
        shape <- as.numeric(sims$shape)

        # Initialize time series of historical aab for fire-fuel feedback
        # effects to be included. Projections start in 2021, leaving 41 years
        # of observed aab to include in this history. Our feedback model relies
        # on a 60 year record, so we simulated the remaining 19 years prior to
        # 1980 based on historical aab from 1980-1999. There is one row for
        # each simulation one column for each year.

        nyr_after_start <- pred_yrs[1] - year[1]
        n_aab_init <- length(w) - nyr_after_start

        prior_aab <- cbind(matrix(rep(aab_init, n_aab_init), ncol = n_aab_init),
                           matrix(rep(aab, N), nrow = N, byrow = TRUE))
        prior_aab <- prior_aab[, seq_along(w)]

        for (yr in pred_yrs) {

            id <- which(data$year == yr)

            # Update prior aab matrix to account for previous years projected
            # aab
            if (yr > pred_yrs[1]) {

                prior_aab <- cbind(prior_aab[, -1], aab_i)

            }

            # Set offset terms for current year
            M_i <- as.numeric(S - (prior_aab %*% as.matrix(w)))
            M_i <- ifelse(M_i > 1, log(M_i), log(1))

            # Model matrix X (only one row for a given year)
            X <- cbind(1, data$bui[id], data$isi[id])

            # Get N estimates of E[area burned] for this single year
            #   X is a 1 x 3 model matrix
            #   betas is a N x 3 matrix of paremeter estimates
            #   M_i is a N x 1 is a vector of offset terms
            #   mu is a N x 1 vector of predictions of aab on a log scale
            mu <- exp(X %*% t(betas) + M_i)

            # Get rate parameters needed for gamma distribution simulation
            rate <- shape / mu

            # simulate a random sample from gamma distribution
            aab_i <- rgamma(N, shape = shape, rate = rate)

            # Cap total amount of area burned that can occur in a given year
            aab_i <- ifelse(aab_i > max_aab, max_aab, aab_i)

            export_mtx[, which(pred_yrs == yr)] <- aab_i

        }

        colnames(export_mtx) <- pred_yrs

        export_fn <- sprintf("future-projections_%s_%s_%s_%d.csv",
            mdl, distr, sim, ecos)

        write.csv(export_mtx,
            file = sprintf("data/model_results/projected_area_burned/%s",
                           export_fn),
            row.names = FALSE)

    }

}
