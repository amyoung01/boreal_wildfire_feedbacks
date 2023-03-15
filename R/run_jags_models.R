#!/usr/bin/env Rscript

# Install required libraries ---------------------------------------------------
suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(fitdistrplus))
suppressPackageStartupMessages(library(R2jags))

# Import arguments -------------------------------------------------------------
args <- commandArgs(trailingOnly = TRUE)
jags_models <- args[seq_along(args)]

# Set working directories ------------------------------------------------------
dataframe_dir <- "./data/dataframes"
results_dir <- "./data/model_results"

# Read in data files -----------------------------------------------------------
aab            <- read.csv(file.path(dataframe_dir,
                                     "annual_area_burned.csv"))
era5           <- read.csv(file.path(dataframe_dir,
                                     "cffdrs-stats_era5_1979-2020.csv"))
ecos_size      <- read.csv(file.path(dataframe_dir,
                                     "ecoregion_size.csv"))
treecov        <- read.csv(file.path(dataframe_dir,
                                     "postfire_forest_growth.csv"))
predictor_vars <- read.csv(file.path(dataframe_dir,
                                     "regression_predictors.csv"))

# Merge climate dataframe and annual area burned data frame --------------------
df <- data.table::merge.data.table(aab, era5, by = c("year", "ecos"))

# Modify annual area burned variable for analysis ------------------------------

# Shorten column name of annual area burned for analysis
names(df)[names(df) == "annual_area_burned_km2"] <- "aab"

# Add small uniform values if total area burned is less than 4 km2 (=400 ha)
df$aab[is.na(df$aab)] <- 0
df$aab[df$aab < 4] <- runif(sum(df$aab < 4), 0, 4)

# Filter by analysis years (1980-2020) and identify unique ecoregions ----------
df <- df[(df$year >= 1980) & (df$year <= 2020), ]
unique_ecos <- unique(df$ecos)

# Initializing Bayesian model runs ---------------------------------------------
n_chains <- 8
burn_in_steps <- 10000
thin_steps <- 80
num_saved_steps <- 2000
n_iter <- ceiling(burn_in_steps + (num_saved_steps * thin_steps) / n_chains)

# Setting up to feedback types to model ----------------------------------------
feedback_type <- c("feedback", "no-feedback")

# For each ecoregion run set of Bayesian GLMs ----------------------------------
for (i in seq_along(unique_ecos)) {

  # Subset data for current ecoregion
  df_i <- df[df$ecos == unique_ecos[i], ]

  # Two options for including feedback curves
  w <- treecov$w[treecov$ecos == unique_ecos[i]]
  w_null <- rep(0, length(w))

  # Size of current ecoregion
  S <- ecos_size$area_km2[ecos_size$ecos == unique_ecos[i]]

  # Maximum Likelihood Estimates (MLE) for lognormal distribution
  aab_ref <- df_i$aab[df_i$year <= 1999]
  aab_ref_mle <- fitdistrplus::fitdist(aab_ref, "lnorm")

  # Get specific predictor variable for given ecoregion
  mdl_form <- predictor_vars$mdl[predictor_vars$ecos == unique_ecos[i]]
  mdl_parts <- strsplit(mdl_form, " ")[[1]]
  isi_var <- mdl_parts[3]
  bui_var <- mdl_parts[5]

  # Data needed to run Bayesian model
  data_list <- list(
    aab = df_i$aab,
    BUI = df_i[[bui_var]],
    ISI = df_i[[isi_var]],
    S = S,
    n = nrow(df_i),
    aab_meanlog = aab_ref_mle$estimate["meanlog"],
    aab_selog = aab_ref_mle$sd["meanlog"]
    )

  # For each model (here using a Gamma distributions)
  for (j in seq_along(jags_models)) {

    jags_model_header <- readLines(jags_models[j], n = 2)
    distr <- strsplit(jags_model_header[[1]], " ")[[1]][-c(1, 2)]
    params_to_save <- strsplit(jags_model_header[[2]], " ")[[1]][-c(1, 2)]

    # Process feedback model and no feedback model
    for (feedback in feedback_type) {

      if (feedback == "feedback") {

        data_list$w <- w

      } else if (feedback == "no-feedback") {

        data_list$w <- w_null

      }

      # Use R2jags package to run Bayesian models
      jags_output <- R2jags::jags(
        data = data_list,
        parameters.to.save = params_to_save,
        model.file = jags_models[j],
        n.chains = n_chains,
        n.iter = n_iter,
        n.burnin = burn_in_steps,
        n.thin = thin_steps,
        quiet = TRUE
        )

      # Add years covered in modeling to jags output for export, will be used
      # in subsequent functions
      jags_output$model$year <- df_i$year

      export_fn <- file.path(results_dir,
                             sprintf("jags-results_%s_%s-model_%d.RData",
                                     distr, feedback, unique_ecos[i]))

      # Save output as RData file
      save(jags_output, file = export_fn)

    }

  }

}
