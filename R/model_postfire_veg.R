#!/usr/bin/env Rscript

# Shape Constrained Additive Models (Version 1.2-13)
suppressPackageStartupMessages(library(scam))

# Range of time since years to consider, values less than lower bound are set to
# 0 and values greater than upper bound are. These values are the how many
# years ago the last fire occurred.
xmin <- -60
xmax <- -5

# Read in perimeter level data to average and model
data <- read.csv("data/dataframes/modis_treecover_postfire.csv")

# Ecoregions to process
ecos <- sort(unique(data$ecos))

# Empty data frame to store results
export_df <- data.frame()

for (i in seq_along(ecos)) { # For each ecoregion ...

  # Subset by all values within current ecoregion
  id <- data$ecos == ecos[i]
  df_i <- data[id, ]

  # Get averages of tree cover as a function of time since fire
  avg_tsf <- aggregate(tree_cover_mean ~ time_of_last_fire,
                       data = df_i,
                       FUN = mean,
                       na.rm = TRUE)

  # Get a table of the number of observations per time since fire value
  samp_size <- table(df_i$time_of_last_fire)
  sampsize_labs <- as.numeric(names(samp_size))

  # Need at least 5 observations to include in growth curve
  id_to_keep <- samp_size > 5 &
                sampsize_labs >= xmin &
                sampsize_labs <= xmax

  tsf_min_sampsize <- sampsize_labs[id_to_keep]

  # Subset to keep observations that have minimum required sample size
  id_to_keep <- avg_tsf$time_of_last_fire %in% tsf_min_sampsize
  avg_tsf <- avg_tsf[id_to_keep, ]

  # Fit monotonically increasing spline function to tree cover data
  fit <- scam::scam(tree_cover_mean ~ s(time_of_last_fire, bs = "mpd", m = 1),
                    data = avg_tsf)

  # Predict values for full range of time since fire values
  # considered (xmin-xmax)
  newdata <- data.frame(time_of_last_fire = seq(xmin, xmax))
  yhat <- scam::predict.scam(fit, newdata = newdata)

  # Rescale fitted values to 0-1 and set zeros as first xmin values
  ymin <- min(yhat)
  ymax <- max(yhat)

  # Convert to weights that scale from 0-1 and add zeros to the last 5 values or
  # most recent fire years
  w <- (yhat - ymin) / (ymax - ymin)
  w <- c(w, rep(0, -1 - xmax))

  # Get inverse of w, as this represents the amount of area removed from the
  # landscape and is no longer available for burning based on time of last fire.
  # Essentially, w represents a weighted value of how much area is removed from
  # the landscape due to the receny of the fire, and the most recen fires remove
  # most of the area.
  w <- 1 - w

  # Put results into data frame
  export_df_i <- data.frame(ecos = rep(ecos[i], length(w)),
                            time_of_last_fire = seq(xmin, -1),
                            w = w)

  export_df <- rbind(export_df, export_df_i)

}

# Export all results to csv file
fn <- "data/dataframes/postfire_successional_functions.csv"
write.csv(export_df, fn, row.names = FALSE)
