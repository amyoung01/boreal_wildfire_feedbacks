library(cffdrs)

test_fwi <- read.csv("test_fwi.csv", sep = ";")

cffdrs_pkg_calcs <- cffdrs::fwi(test_fwi, lat.adjust = FALSE)
pydata <- read.csv("cffdrs_from_py.csv")

png("test_cffdrs.png", width = 6.5, height = 4.5,
    units = "in", res = 450)

par(mfrow = c(2, 3))

plot(pydata$ffmc, cffdrs_pkg_calcs$FFMC,
     xlab = "Python package", ylab = "R Package",
     xlim = c(0, 101), ylim = c(0, 101),
     main = "Fine Fuel Moisture Code")
abline(a = 0, b = 1)

plot(pydata$dmc, cffdrs_pkg_calcs$DMC,
     xlab = "Python package", ylab = "R Package",
     xlim = c(0, 100), ylim = c(0, 100),
     main = "Duff Moisture Code")
abline(a = 0, b = 1)

plot(pydata$dc, cffdrs_pkg_calcs$DC,
     xlab = "Python package", ylab = "R Package",
     xlim = c(0, 150), ylim = c(0, 150),
     main = "Drought Code")
abline(a = 0,b = 1)

plot(pydata$isi, cffdrs_pkg_calcs$ISI,
     xlab = "Python package", ylab = "R Package",
     xlim = c(0, 40), ylim = c(0, 40),
     main = "Initial Spread Index")
abline(a = 0, b = 1)

plot(pydata$bui, cffdrs_pkg_calcs$BUI,
     xlab = "Python package", ylab = "R Package",
     xlim = c(0, 100), ylim = c(0, 100),
     main = "Build-up Index")
abline(a = 0, b = 1)

dev.off()
