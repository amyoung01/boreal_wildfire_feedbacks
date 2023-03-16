import subprocess

jags_rscript = 'R/run_jags_models.R'
jags_model = 'R/aab_bayesian_gamma_regression.txt'

subpr_call = 'Rscript --vanilla %s %s' % (jags_rscript, jags_model)

subpr_call = subpr_call.split(" ")

subprocess.run(subpr_call)
