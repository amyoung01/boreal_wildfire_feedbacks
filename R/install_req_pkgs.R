#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(remotes))

args <- commandArgs(trailingOnly = TRUE)
env_libpath <- args[1]

list_of_packages <- c("actuar", "fitdistrplus", "scam", "R2jags")
install.packages(list_of_packages, env_libpath,
                 repos = "https://cloud.r-project.org", quiet = TRUE)
