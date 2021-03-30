#! /usr/bin/python3
#
# ██████ █████     ██████  ██████ ██████ ██ ███    ███ ██ ███████ ██████ ██████
# ██    ██   ██   ██    ██ ██   ██  ██   ██ ████  ████ ██    ███  ██     ██   ██
# █████ ███████   ██    ██ ██████   ██   ██ ██ ████ ██ ██   ███   █████  ██████ 
# ██    ██   ██   ██    ██ ██       ██   ██ ██  ██  ██ ██  ███    ██     ██   ██
# █████ ██   ██    ██████  ██       ██   ██ ██      ██ ██ ███████ ██████ ██   ██
# FOR MUSICAL ONSET DETECTION
#
#  Author:  Domenico Stefani
#           (domenico.stefani@unitn.it)
#           (https://orcid.org/0000-0002-2126-0667)
#  Date:    16th March 2021

#                     OPTIMIZATION OF AUBIO ONSET PARAMETERS
#                             (https://aubio.org/)
#
# This instance of the optimizer uses AubioOnset which has a series of fixed
# parameters and 2 which are free and have to be optimized.
# To parallelize the computation (in a naive way) this optimizer is called for
# each combination of buffer_size and onset_method on separate terminals.
# This is possible since the evaluator script allows concurrent execution
#
# NOTE: It would be better to parallelize the evaluation of solutions internally
#       (in this script) and it can theoretically be done since INSPYRED is
#       compatible with both the multiprocessing module and the pp (parallel
#       python) module.
#       I wasn't able to get MP to work (pickling issue) while PP run apparently
#       smoothly, but it always stopped at the same generation without throwing
#       any error (clean logs)
#       Note that the "stopping" generation would change when changing the
#       number of processes to spawn.

# #----------------------------------------------------------------------------#
# # (Current) Problem Formalization                                            #
# #----------------------------------------------------------------------------#
#
# Fixed parameters:
# - Hop size        (64 samples in our case)
# - Buffer Size     (64,128,256,512,1024 or 2048 samples depending on the run)
# - Onset Method    (all the aubio onset methods in aubio, plus mkl without
#                    adaptive whitening)
# - Min IoI         (20 ms in our case)

# #----------------------------------------------------------------------------#
# # Evolutionary Problem Formulation                                           #
# #----------------------------------------------------------------------------#
#
# The evolutionary computation algorithm creates a population in which each
# individual represents a candidate solution of the problem. In our case an
# individual is simply an array of parameter values (2 precisely) and this is
# also referred to as the genotype (metaphor to real genetics)
# The phenotype is instead the manifestation of the genotype, and in this case
# it consists in a performance metric which is the result of the execution of
# onset detector at hand, with the paremeters specified in the current genotype.
# It is commonly referred to as fitness of a solution.
#
# Solutions are EVOLVED in generations and they can undergo Mutation and
# Crossover. Mutation takes a single individual and generates an offsprint by
# changing its genotype. Crossover takes 2 solutions/individuals and produces
# offsprings by combination (many different mutation&crossover operators can be
# used).
#
# Genotype: (free parameters)
# - Silence Threshold
# - Onset Threshold
#
# Phenotype:
# - macro avg. f1-score (avg. f1-score across each playng technique in the
#                        dataset used for the study)

import inspyred             # Evoliutionary Computation Framework
import computeLatency       # My own evaluation script for Aubio
import pylab                # For plots
from random import Random
import sys
import os

PARALLEL = False            # Failed tentative of internal parallelization
RESFOLDER="evolutionaryOptimizerResults/"

# """--Parameters for Aubio -------------------------------------------------"""
AUDIO_DIRECTORY = "audiofiles"      # Dir. in which audio files are contained
AUBIOONSET_COMMAND = "aubioonset"   # OD executable
default_onset_method = "hfc"        # Default Aubio OD method
default_buffer_size = 64            # Default Aubio OD Buffer Size
HOP_SIZE = 64                       # Aubio OD hop size
MIN_IOI = 0.02                      # Min Inter-Onset-Interval (onset debounce)

# """--Initialization Boundaries for the Free Parameters --------------------"""
MIN_ONSET_THRESH   = 0.1
MAX_ONSET_THRESH   = 3.6
MIN_SILENCE_THRESH = -60
MAX_SILENCE_THRESH = -30

# """--Parameters for the Evolutionary Algorithm ----------------------------"""

# THESE WORK (with arithmetic_crossover & gaussian_mutation) but not optimal
# populationSize = 6
# numberOfGenerations = 30
# numberOfEvaluations = 2500                  # used with evaluation_termination
# tournamentSize = 3
# mutationRate = 0.7
# gaussianMean = 0
# gaussianStdev = 1.0
# crossoverRate = 0.9
# selectionSize = populationSize
# numElites = 0


populationSize = 10                 # Number of solutions in each generation
numberOfGenerations = 30
tournamentSize = 4                  # See Tournament Selection
mutationRate = 0.7                  # Rate of mutation operators
gaussianMean = 0                    # Mean for gaussian mutation
gaussianStdev = 3.0                 # stdev for gaussian mutation
crossoverRate = 0.7                 # Rate of crossover operation
selectionSize = populationSize
numElites = 1                       # See elitim (n best solutions kept in gen.)

# """--Visualization---------------------------------------------------------"""
display = True

# """------------------------------------------------------------------------"""
class ConfigurationEvaluator():
    def __init__(self,rng,aubioparameters):
        self.rng = rng       # Pre inizialized pseudo-random generator
                             # (to preserve eventual fixed seed)
        self.bounder = None  # A bounding operator with adequate values can be
                             # used
        self.maximize = True # Flag to define the problem nature
        self.aubioparameters = aubioparameters

    ## Generator method
    #  This generates new individuals randomly
    def generator(self, random, args):
        onset_threshold = self.rng.uniform(MIN_ONSET_THRESH, MAX_ONSET_THRESH)
        silence_threshold = self.rng.uniform(MIN_SILENCE_THRESH, MAX_SILENCE_THRESH)
        return [onset_threshold,silence_threshold]

    ## Evaluator method
    #  This evaluates the fitness of the given individual/s (@candidates)
    def evaluator(self, candidates, args):
        fitness = []
        for candidate in candidates:
            onset_threshold = candidate[0]
            silence_threshold = candidate[1]
            info, metrics = computeLatency.perform_main_analysis(audio_directory = self.aubioparameters['audio_directory'],
                                                                 aubioonset_command = self.aubioparameters['aubioonset_command'],
                                                                 onset_method = self.aubioparameters['onset_method'],
                                                                 buffer_size = self.aubioparameters['buffer_size'],
                                                                 hop_size = self.aubioparameters['hop_size'],
                                                                 silence_threshold = silence_threshold,
                                                                 onset_threshold = onset_threshold,
                                                                 minimum_inter_onset_interval_s = self.aubioparameters['minimum_inter_onset_interval_s'],
                                                                 max_onset_difference_s = self.aubioparameters['max_onset_difference_s'],
                                                                 do_ignore_early_onsets = self.aubioparameters['do_ignore_early_onsets'],
                                                                 samplerate = self.aubioparameters['samplerate'],
                                                                 failsafe = self.aubioparameters['failsafe'],
                                                                 save_results=False)
            if metrics:
                fitness_c  = metrics["macroavg_tech_metrics"]["f1-score"]
            else:
                fitness_c = 0
            fitness.append(fitness_c)
        return fitness

def main(rng, onset_method=default_onset_method, buffer_size=default_buffer_size, display=False, runstring=""):
    # Initialization of some aubio parameter
    aubioonset_command = AUBIOONSET_COMMAND
    real_onset_method = onset_method
    # Trick that changes executable if mkl without whitening is selected
    # If the exec is not compatible it can be compiled from aubio src by
    # changing Adaptive Whitening to always be off (or at least when
    # initializing the mkl method)
    if onset_method == "mkl(noaw)":
        print("Disabling whitening")
        onset_method = "mkl"
        aubioonset_command = "./utility_scripts/customAubio/aubioonset-mkl-nowhitening"
    # Parameter initialization
    aubioparameters = {"audio_directory" : AUDIO_DIRECTORY,
                       "aubioonset_command" : aubioonset_command,
                       "onset_method" : onset_method,
                       "buffer_size" : buffer_size,
                       "hop_size" : HOP_SIZE,
                       "minimum_inter_onset_interval_s" : MIN_IOI,
                       "max_onset_difference_s" : 0.02,
                       "do_ignore_early_onsets" : True,
                       "samplerate" : 48000,
                       "failsafe" : True,
                       "real_onset_method":real_onset_method}
    # Create an instance of the problem and feed the current pseudo-random
    # generator
    problem = ConfigurationEvaluator(rng,aubioparameters)

    # - INSPYRED INITIALIZATION ---------------------------------------------- #

    # the evolutionary algorithm (EvolutionaryComputation is a fully
    # configurable evolutionary algorithm)
    # standard GA, ES, SA, DE, EDA, PAES, NSGA2, PSO and ACO are also available
    ea = inspyred.ec.EvolutionaryComputation(rng)

    # observers: provide various logging features
    # if display:
    ea.observer = [#inspyred.ec.observers.stats_observer,
                   inspyred.ec.observers.file_observer,
                   inspyred.ec.observers.plot_observer
                    #inspyred.ec.observers.best_observer,
                    #inspyred.ec.observers.population_observer
                  ]

    # Selection operator
    # ea.selector = inspyred.ec.selectors.truncation_selection
    # ea.selector = inspyred.ec.selectors.uniform_selection
    # ea.selector = inspyred.ec.selectors.fitness_proportionate_selection
    # ea.selector = inspyred.ec.selectors.rank_selection
    ea.selector = inspyred.ec.selectors.tournament_selection

    # variation operators (mutation/crossover)
    ea.variator = [inspyred.ec.variators.arithmetic_crossover,
                #    inspyred.ec.variators.blend_crossover,
                #    inspyred.ec.variators.heuristic_crossover,
                   inspyred.ec.variators.laplace_crossover,
                # #    inspyred.ec.variators.simulated_binary_crossover,
                   inspyred.ec.variators.gaussian_mutation,
                #    inspyred.ec.variators.nonuniform_mutation
                   ]

    # Replacement operator
    # ea.replacer = inspyred.ec.replacers.truncation_replacement
    # ea.replacer = inspyred.ec.replacers.steady_state_replacement
    # ea.replacer = inspyred.ec.replacers.random_replacement
    # ea.replacer = inspyred.ec.replacers.plus_replacement
    # ea.replacer = inspyred.ec.replacers.comma_replacement     # Has no elitism
    # ea.replacer = inspyred.ec.replacers.crowding_replacement
    # ea.replacer = inspyred.ec.replacers.simulated_annealing_replacement
    # ea.replacer = inspyred.ec.replacers.nsga_replacement
    # ea.replacer = inspyred.ec.replacers.paes_replacement
    ea.replacer = inspyred.ec.replacers.generational_replacement

    # termination condition
    # ea.terminator = inspyred.ec.terminators.evaluation_termination
    # ea.terminator = inspyred.ec.terminators.no_improvement_termination
    # ea.terminator = inspyred.ec.terminators.diversity_termination
    # ea.terminator = inspyred.ec.terminators.time_termination
    ea.terminator = inspyred.ec.terminators.generation_termination

    # ------------------------------------------------------------------------ #
    # Initialize log files
    _statfile = open(RESFOLDER+"inspyred-statistics-"+runstring+".txt","a")
    _indfile = open(RESFOLDER+"inspyred-individuals-"+runstring+".txt","a")

    # Parameters for multiprocessing (CURRENTLY NOT WORKING)
    # https://pythonhosted.org/inspyred/examples.html#evaluating-individuals-concurrently
    #
    # These can be added in ea.evolve as args (But do not work yet)
    #
    # evaluator=inspyred.ec.evaluators.parallel_evaluation_mp
    # mp_evaluator=problem.evaluator
    # mp_num_cpus=1

    if PARALLEL:
        # Parameters for Parallel execution (CURRENTLY NOT WORKING)
        # For some reason the computation stops at a set generation without
        # Throwing errors.
        # The generation at which it stops depends on pp_nprocs
        final_pop = ea.evolve(generator=problem.generator,
                              evaluator=inspyred.ec.evaluators.parallel_evaluation_pp,
                              pp_evaluator=problem.evaluator,
                              pp_dependencies=(computeLatency.perform_main_analysis,),
                              pp_modules=("computeLatency",),
                              pp_nprocs=12,
                              bounder=problem.bounder,
                              maximize=problem.maximize,
                              pop_size=populationSize,
                              max_generations=numberOfGenerations,
                              #max_evaluations=numberOfEvaluations,
                              tournament_size=tournamentSize,
                              mutation_rate=mutationRate,
                              gaussian_mean=gaussianMean,
                              gaussian_stdev=gaussianStdev,
                              crossover_rate=crossoverRate,
                              num_selected=selectionSize,
                              num_elites=numElites,
                              statistics_file = _statfile,
                              individuals_file =_indfile)
    else:
        # Standard single-thread optimizer (WORKING)
        final_pop = ea.evolve(generator=problem.generator,
                              evaluator=problem.evaluator,
                              bounder=problem.bounder,
                              maximize=problem.maximize,
                              pop_size=populationSize,
                              max_generations=numberOfGenerations,
                              max_evaluations=numberOfEvaluations,
                              tournament_size=tournamentSize,
                              mutation_rate=mutationRate,
                              gaussian_mean=gaussianMean,
                              gaussian_stdev=gaussianStdev,
                              crossover_rate=crossoverRate,
                              num_selected=selectionSize,
                              num_elites=numElites,
                              statistics_file = _statfile,
                              individuals_file =_indfile)

    _statfile.close()
    _indfile.close()

    if display:
        final_pop.sort(reverse=True)
        print(final_pop[0])
        best_onset_threshold = final_pop[0].candidate[0]
        best_silence_threshold = final_pop[0].candidate[1]

        # When the best solution is found, these parameters are used to compute
        # once again all the other metrics (latency, accuracy, recall,...)
        info, metrics = computeLatency.perform_main_analysis(audio_directory = aubioparameters['audio_directory'],
                                                             aubioonset_command = aubioparameters['aubioonset_command'],
                                                             onset_method = aubioparameters['onset_method'],
                                                             buffer_size = aubioparameters['buffer_size'],
                                                             hop_size = aubioparameters['hop_size'],
                                                             onset_threshold = best_onset_threshold,
                                                             silence_threshold = best_silence_threshold,
                                                             minimum_inter_onset_interval_s = aubioparameters['minimum_inter_onset_interval_s'],
                                                             max_onset_difference_s = aubioparameters['max_onset_difference_s'],
                                                             do_ignore_early_onsets = aubioparameters['do_ignore_early_onsets'],
                                                             samplerate = aubioparameters['samplerate'],
                                                             failsafe = aubioparameters['failsafe'])
        # Call an utility that creates a pretty string for the current solution
        # with all the metrics (this can be pasted into excel)
        res = computeLatency.create_string(info = info,
                                           metrics = metrics,
                                           use_oldformat=False,
                                           do_copy = True,
                                           failsafe = True)
        print(res) # Print the metrics
        # Write the metrics to file
        resfile = open(RESFOLDER+"best-"+aubioparameters['real_onset_method'] +"-"+str(aubioparameters['buffer_size'])+"res.txt","w")
        resfile.write(res+"\n")
        resfile.close()

# Usage: evolutionaryOptimizer <random seed> <onset_method> <buffer_size>
if __name__ == "__main__":
    if len(sys.argv) == 4 :
        rng = Random(int(sys.argv[1]))
        _method = sys.argv[2]
        _bufsize = int(sys.argv[3])
    else:
        print("Error! Wrong number of arguments")
        print("Usage: "+sys.argv[0]+" <seed> <onset_method> <buffer_size>")
        exit()

    os.system("mkdir -p "+RESFOLDER)

    import time
    # Create a string with the time of this execution (to avoid file overwrite)
    runstring = str(_method)+"-"+str(_bufsize)+"-"+time.strftime("%Y%m%d-%H%M%S")

    # Logging snipped directly from Inspyred docs
    import logging
    logger = logging.getLogger('inspyred.ec')
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('inspyred.log', mode='w')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Call the main method
    main(rng,onset_method=_method, buffer_size=_bufsize,display=display, runstring=runstring)

    # Save the resuting plot
    if display:
        pylab.ioff()
        print(runstring)
        pylab.savefig(RESFOLDER+runstring)
