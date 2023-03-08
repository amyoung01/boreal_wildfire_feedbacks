# -----------------------------------------------------------------------------
# Initialize workspace
# -----------------------------------------------------------------------------
rm(list = ls()) # Remove variables from current environment

# TODO: how to read in config.yaml file into R
gcms <- c("EC-Earth3-Veg", "MPI-ESM1-2-HR", "MRI-ESM2-0", "CNRM-CM6-1-HR")

# -----------------------------------------------------------------------------
# Read in list of model files 
# -----------------------------------------------------------------------------
setwd("data/model_results")
files <- list.files(pattern = "\\.RData$")

ecos_size <- "data/dataframes/ecoregion_size.csv"
ecos_size <- read.csv(ecos_size)

unique_ecos = ecos_size$ecos

pred_yrs <- 2021:2099

max_frac <- 6

# -----------------------------------------------------------------------------
# Make projections of future area burned for each gcm
# -----------------------------------------------------------------------------
for (mdl in gcms){

    pred_vars_file <- sprintf("data/dataframes/cffdrs-stats_%s_1980-2099.csv",
                               mdl)
    pred_vars <- read.csv(pred_vars_file)

    for (f in seq_along(files)){

        setwd("data/model_results")

        file_i <- files[f]
        jags_results <- load(file_i)

        file_name <- strsplit(file_i, "\\.")[[1]][1]
        file_parts <- strsplit(file_name, "_")[[1]]
        distr <- file_parts[2]
        sim <- file_parts[3]
        ecos <- as.numeric(file_parts[4])

        pred_vars_i <- pred_vars[pred_vars$ecos == ecos, ]
        data <- data.frame(year = pred_vars_i$year,
                        bui = pred_vars_i$bui_95d,
                        isi = pred_vars_i$isi_max)

        aab <- jags_output$model$data()$aab
        w <- jags_output$model$data()$w
        S <- jags_output$model$data()$S

        sims <- jags_output$BUGSoutput$sims.list
        beta0 <- sims$beta0
        beta1 <- sims$beta1
        beta2 <- sims$beta2
        betas <- cbind(beta0,
                       beta1,
                       beta2)

        aab_init <- sims$aab_init

        max_aab <- max_frac * max(aab)

        N <- length(beta0)

        export_mtx <- matrix(NA, nrow = N, ncol = length(pred_yrs))

        prior_aab <- matrix(NA,nrow=N,ncol=60)
        for (p in 1:N){
            prior_aab[p, ] <- c(rep(aab_init[p], 19), aab)
        }

        for (yr in 2021:2099){

            id <- which(pred_vars_i$year == yr)

            if (yr > pred_yrs[1]){

                prior_aab <- cbind(prior_aab[, -1], aab_i)

            }

            M_i <- S - (prior_aab %*% as.matrix(w))
            M_i <- ifelse(M_i > 1, log(M_i), log(1))

            X <- as.matrix(rbind(
                            1,
                            pred_vars_i$bui_95d[id],
                            pred_vars_i$isi_max[id]
                        ))

            mu <- betas %*% X + M_i

            if (distr == "Gamma") {

                shape <- sims$shape
                rate <- shape / exp(mu)

                aab_i <- rgamma(N, shape = shape, rate = rate)

            } else if (distr == "Lognormal") {

                sdlog <- sims$sdlog

                aab_i <- rlnorm(N, meanlog = mu, sdlog = sdlog)

            }

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