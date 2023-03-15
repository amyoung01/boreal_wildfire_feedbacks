#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(remotes))

list_of_packages <- c("actuar", "car", "data.table", "fitdistrplus", "R2jags",
                      "scam")
list_of_pkgversions <- list(actuar = "3.3-1", car = "3.1-1",
                            data.table = "1.14.6", fitdistrplus = "1.1-8",
                            R2jags = "0.7-1", scam = "1.2-13")

for (pkg in list_of_packages) {

  remotes::download_version(pkg, version = list_of_pkgversions[[pkg]],
                            repos = "https://cloud.r-project.org")

}
