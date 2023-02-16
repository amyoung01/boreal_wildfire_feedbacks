# Initialize workspace
rm(list = ls()) # Remove variables from current environment

# Install required libraries
library(R2jags) # Using R to Run 'JAGS' (Version: 0.7-1)
library(envDocument)

# Get directory of R script (https://stackoverflow.com/a/16046056)
# wdir <- dirname(parent.frame(2)$ofile) #getwd() #dirname(sys.frame(1)$ofile)
cat(env_doc("print"))
# dataframes_dir <- paste0(wdir, "/../data/dataframes")
# model_results_dir <- paste0(wdir, "/../data/model_results")

# model_yrs <- 1980:2020

# aab <- read.csv(paste0(dataframes_dir, "annual_area_burned.csv"))
# era5 <- read.csv(paste0(dataframes_dir, "cffdrs_stats_era5_1979-2020.csv"))
# treecov <- read.csv(paste0(dataframes_dir, "postfire_forest_growth.csv"))

# lnorm_model <- paste0(wdir, "/aab_bayesian_lognormal_regression.txt")
# gamma_model <- paste0(wdir, "/aab_bayesian_gamma_regression.txt")

# data <- read.csv(data_table_file)
# postfire_regrowth = read.csv(postfire_regrowth_file)
# ecos_size <- read.csv(ecos_size_file)

# unique_ecos = unique(data$ecos)

# data$aab[data$aab<=4] <- runif(sum(data$aab<=4),0,4)

# nChains <- 8
# burnInSteps <- 10000
# thinSteps <- 80
# numSavedSteps <- 2000
# nIter <- ceiling(burnInSteps + (numSavedSteps * thinSteps)/nChains)

# gamma_params_to_save <- c("beta0",
#                           "beta1",
#                           "beta2",
#                           "shape",
#                           "aab_init",
#                           "M")

# lnorm_params_to_save <- c("beta0",
#                           "beta1",
#                           "beta2",
#                           "sdlog",
#                           "aab_init",
#                           "M")

# for (i in 1:length(unique_ecos)){
  
#   df_i <- data[data$ecos == unique_ecos[i],]; rownames(df_i) <- NULL
#   w <- postfire_regrowth$w[postfire_regrowth$ecos == unique_ecos[i]]
#   w_null <- rep(0,length(w))
  
#   S <- ecos_size$area_km2[ecos_size$ecos == unique_ecos[i]]
  
#   # Maximum Likelihood Estimates (MLE) for lognormal model
#   aab_ref <- df_i$aab[(df_i$yr >= 1980) & (df_i$yr <= 1999)]
#   aab_ref_mle <- fitdistrplus::fitdist(aab_ref,"lnorm")
  
#   data_list_i <- list(aab = df_i$aab,
#                       BUI = df_i$bui_fs_avg,
#                       ISI = df_i$isi_max_avg,
#                       w = w,
#                       S = S,
#                       n = nrow(df_i),
#                       aab_meanlog = aab_ref_mle$estimate["meanlog"],
#                       aab_selog = aab_ref_mle$sd["meanlog"])
  
#   aab_lnorm_feedback <- jags(data = data_list_i,
#                              parameters.to.save = lnorm_params_to_save,
#                              model.file = lnorm_model,
#                              n.chains = nChains,
#                              n.iter = nIter,
#                              n.burnin = burnInSteps,
#                              n.thin = thinSteps)
  
#   aab_gamma_feedback <- jags(data = data_list_i,
#                              parameters.to.save = gamma_params_to_save,
#                              model.file = gamma_model,
#                              n.chains = nChains,
#                              n.iter = nIter,
#                              n.burnin = burnInSteps,
#                              n.thin = thinSteps)
  
#   data_list_i$w <- w_null
  
#   aab_lnorm_nofeedback <- jags(data = data_list_i, 
#                                parameters.to.save = lnorm_params_to_save,
#                                model.file = lnorm_model, 
#                                n.chains = nChains, 
#                                n.iter = nIter, 
#                                n.burnin = burnInSteps, 
#                                n.thin = thinSteps)
  
#   aab_gamma_nofeedback <- jags(data = data_list_i, 
#                                parameters.to.save = gamma_params_to_save,
#                                model.file = gamma_model, 
#                                n.chains = nChains, 
#                                n.iter = nIter, 
#                                n.burnin = burnInSteps, 
#                                n.thin = thinSteps)
  
#   lognormal_feedback_file <- sprintf("%s/results/regression_results/full_model/lognormal_feedback_%d.RData",wdir,unique_ecos[i])
#   gamma_feedback_file <- sprintf("%s/results/regression_results/full_model/gamma_feedback_%d.RData",wdir,unique_ecos[i])
#   lognormal_nofeedback_file <- sprintf("%s/results/regression_results/full_model/lognormal_no-feedback_%d.RData",wdir,unique_ecos[i])
#   gamma_nofeedback_file <- sprintf("%s/results/regression_results/full_model/gamma_no-feedback_%d.RData",wdir,unique_ecos[i])
  
#   save(aab_lnorm_feedback,file=lognormal_feedback_file)
#   save(aab_gamma_feedback,file=gamma_feedback_file)
#   save(aab_lnorm_nofeedback,file=lognormal_nofeedback_file)
#   save(aab_gamma_nofeedback,file=gamma_nofeedback_file)
  
# }