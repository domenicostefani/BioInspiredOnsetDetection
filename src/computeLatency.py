#!/usr/bin/env python3
#
#  █████  ██    ██ ██████  ██  ██████   ██████  ███    ██ ███████ ███████ ██████ 
# ██   ██ ██    ██ ██   ██ ██ ██    ██ ██    ██ ████   ██ ██      ██        ██    
# ███████ ██    ██ ██████  ██ ██    ██ ██    ██ ██ ██  ██ ███████ █████     ██ 
# ██   ██ ██    ██ ██   ██ ██ ██    ██ ██    ██ ██  ██ ██      ██ ██        ██ 
# ██   ██  ██████  ██████  ██  ██████   ██████  ██   ████ ███████ ███████   ██ 
#
# ███████ ██    ██  █████  ██     ██    ██  █████ ████████  ██████  ██████ 
# ██      ██    ██ ██   ██ ██     ██    ██ ██   ██   ██    ██    ██ ██   ██ 
# █████   ██    ██ ███████ ██     ██    ██ ███████   ██    ██    ██ ██████  
# ██       ██  ██  ██   ██ ██     ██    ██ ██   ██   ██    ██    ██ ██   ██ 
# ███████   ████   ██   ██ ███████ ██████  ██   ██   ██     ██████  ██   ██ 
#
# This script computes a numer of metrics on the performance of AubioOnset on a
# specific set of recordings (individual sounds from acoustic guitars)
# It can be used to manually optimize the input parameters on the dataset,
# or it can be used in conjuction with an automatic optimizer, such as the
# Evolutionary computation one, contained in "./evolutionaryoptimizer.py"
#
# ** This is intended to be used with different support scripts contained in
#    "./utility_scripts/"
#
# This script does multiple things:
# - It asks the user for the parameters for AUBIOONSET
# - It calls "extractAllOnsets.sh" with those parameters, which calls aubioonset
#   on all the WAV files in the folder
# - It compares the onsets labeled with the ones extracted
#   When computing the delay, it sums the delay value that AUBIOONSET regularly
#   subtracts to the detection time, to center the distribution around 0
# - It finally calls a R analysis script to plot the delay distribution and the
#   metrics (Accuracy, Precision, Recall)
#
# Author: Domenico Stefani
#         domenico.stefani[at]unitn.it
#         domenico.stefani96[at]gmail.com
# Date:   10th Nov 2020
#
##
_VERBOSE = False # Print info

import glob             # To read folder filelist
import os               # To call scripts
import re               # Regexp, to parse script results
from enum import Enum   # To specify parameter type
import sys
import tempfile         # It allows to have univoque tmp dirs for each run
                        # (To allow parallel execution)

## Function that performs the analysis and compute all the relevant metrics
#
#  @param audio_directory                : Directory containing audio files
#  @param aubioonset_command             : Exec. for aubio to use
#  @param onset_method                   : Aubioonset method to use
#  @param buffer_size                    : Buffer size for Aubioonset (samples)
#  @param hop_size                       : Hop size for Aubioonset (samples)
#  @param silence_threshold              : Threshold of silence (dB)
#  @param onset_threshold                : Dyn. Onset threshold
#  @param minimum_inter_onset_interval_s : Onset "debounce" in seconds
#  @param max_onset_difference_s         : Acceptation window for detected onset
#  @param do_ignore_early_onsets         : Ignore onsets detected before label
#  @param samplerate                     : Audio Sample rate
#  @param failsafe                       : Avoid raising errors if True
#  @param save_results                   : Keep record of results in a file
#
#  @return It returns a dict with parameters and one with metrics
#
def perform_main_analysis(audio_directory,aubioonset_command,onset_method,buffer_size,hop_size,silence_threshold,onset_threshold,minimum_inter_onset_interval_s,max_onset_difference_s=0.02,do_ignore_early_onsets=True,samplerate=48000, failsafe=True,save_results=True):
    with tempfile.TemporaryDirectory(prefix="aubioonsetanalysis-") as TEMP_FOLDER:
        TEMP_FOLDER=TEMP_FOLDER+"/"
        ONSETS_EXTRACTED_DIR = TEMP_FOLDER+"onsets_extracted/"
        ONSETS_LABELED_DIR="onsets_labeled/"    # This is not in the temp folder
        LOGRES_DIR = "results/"

        # Create the option string with the parameter values specified
        opts = " -C " + str(aubioonset_command) + \
               " -B " + str(buffer_size) + \
               " -H " + str(hop_size) + \
               " -s " + str(silence_threshold) + \
               " -t " + str(onset_threshold) + \
               " -O " + str(onset_method) + \
               " -M " + str(minimum_inter_onset_interval_s) + \
               " -e " + str(TEMP_FOLDER) + \
               " -d " + audio_directory + "/" + ""

        # Call onset extraction routine
        COMMAND = "./utility_scripts/extractAllOnsets.sh " + opts
        if _VERBOSE:
            print("Calling "+COMMAND)
        EXT_RES = os.popen(COMMAND).read()

        if re.search("line",EXT_RES) != None:
            print("Error in extractOnset.sh: " + str(re.search("extractOnset.sh: line",EXT_RES).group(0)))

        # Parse script output, looking for the AUBIOONSET delay (in samples)
        '''
            Aubioonset computes the onset time by subtracting a fixed time
            period to the detection time.
            We are interested in the detection time, so we add to the reported
            time, the delay parameter used.
            Since the parameter is set inside of aubio, for the time being we
            compute the delay depending on the input parameters, in the same way
            that aubio does it.
            NB: this is susceptible to changes in Aubio, it should be improved
        '''
        PARTIAL_STRING = re.search("To get the real detection time, add the delay of [0-9]+ samples",EXT_RES).group(0)

        AUBIODELAY_SAMPLES = int(re.search('[0-9]+', PARTIAL_STRING).group(0))
        AUBIODELAY_S = AUBIODELAY_SAMPLES * 1.0 / samplerate
        if _VERBOSE:
            print("The delay introduced by aubioonset is " + str(AUBIODELAY_SAMPLES) + " samples")
            print("Delay in ms " + str(AUBIODELAY_S*1000.0))

        # Strings for CSV separator and Not-a-Number values
        SEP_STR = ","   # separator
        NAN_STR = "NAN" # NaN

        # Compare the onsets in @labels_file and @extracted_file, compute the delay and
        # write the result as a CSV to out_file
        def computeDifference(recording_name,labels_file,extracted_file,out_file):
            end_flag = False                     # termination flag
            lbl_line = labels_file.readline()    # read the very first line
            ext_line = extracted_file.readline() # read the very first line
            while not end_flag:
                if lbl_line == "" and ext_line == "": # Terminate when both are EOF
                    end_flag = True
                else:
                    # Convert to float or set to infinity if EOF
                    lbl_value = float(lbl_line.split()[0] if (lbl_line != "") else "inf")
                    ext_value = float(ext_line.split()[0] if (ext_line !="") else "inf")
                    # Compute the delay in seconds and sum AUBIOONSET delay
                    diff = ext_value - lbl_value + AUBIODELAY_S
                    # Skip values if onsets are different (delay greater than threshold)
                    if abs(diff) < max_onset_difference_s and (not do_ignore_early_onsets or diff > 0):
                        out_file.write(str(lbl_value) + SEP_STR + str(ext_value) + SEP_STR + str(diff) + SEP_STR + recording_name + "\n")
                        lbl_line = labels_file.readline()
                        ext_line = extracted_file.readline()
                    elif lbl_value < ext_value:
                        out_file.write(str(lbl_value) + SEP_STR + NAN_STR + SEP_STR + NAN_STR + SEP_STR + recording_name + "\n")
                        lbl_line = labels_file.readline()
                    elif lbl_value > ext_value:
                        out_file.write(NAN_STR + SEP_STR + str(ext_value) + SEP_STR + NAN_STR + SEP_STR + recording_name + "\n")
                        ext_line = extracted_file.readline()
        # This functions uses pattern search to find a file with a similar name to the one specified.
        # For similar I mean a file in the same folder, with the same extension,
        # beginning with the same name but (potentially) with more characters after the
        # original name. Example:
        # filename = "somefolder/somefilename.txt"
        # found    = "somefolder/somefilename_secondversion.txt"
        # "found" IS CONSIDERED A SIMILAR FILENAME
        def find_similar_file(filename):
            filenameonly = filename[:-4]
            extonly = filename[-4:]
            searchpattern = filenameonly + "*" + extonly
            filesfound = glob.glob(searchpattern)
            # Terminate if NO file found, or more than one found
            if len(filesfound) != 1:
                raise Exception("Found "+str(len(filesfound))+" similar files instead of 1 (\""+filename+"\")")
            return filesfound[0]

        onsets_labeled = glob.glob("onsets_labeled/*.txt")
        # Open output file
        OUT_DIR = TEMP_FOLDER+"output/"
        os.system("mkdir -p "+OUT_DIR)
        DELAYS_FILE=OUT_DIR+"onset_delay.csv"
        output_csv = open(DELAYS_FILE, "w")
        # Write CSV header
        output_csv.write("onset_labeled" + SEP_STR + "onset_extracted" + SEP_STR + "difference" + SEP_STR + "recording\n")

        # Iterate over all label files and call computeDifference() for all files
        for filename in onsets_labeled:
            filename = os.path.basename(filename)
            file_labels = open(ONSETS_LABELED_DIR+filename, "r")
            file_extrac = open(find_similar_file(ONSETS_EXTRACTED_DIR+filename), "r")
            computeDifference(filename,file_labels,file_extrac,output_csv)
            file_labels.close()
            file_extrac.close()

        output_csv.close()

        # Call analysis script
        logres_filename = LOGRES_DIR+"res_"+\
                          onset_method+"_"+\
                          str(buffer_size)+"_"+\
                          str(hop_size)+"_"+\
                          str(silence_threshold)+"_"+\
                          str(onset_threshold)+"_"+\
                          str(minimum_inter_onset_interval_s)+".log"

        os.system("mkdir -p "+LOGRES_DIR)
        os.system("Rscript utility_scripts/r_analysis/analize_delays.r "+DELAYS_FILE+" > "+logres_filename)

        def process_R_results(results_filename):
            glob_metrics = dict.fromkeys(["accuracy","precision","recall","f1-score"])
            for metric in glob_metrics.keys():
                glob_metrics[metric] = float(os.popen("cat " + results_filename + '| grep -P \"\\\"'+metric+': [0-9]\.[0-9]+\\\"\"' + '| grep -P -o \"[0-9]\.[0-9]+\"').read())

            macroavg_metrics = dict.fromkeys(["accuracy","precision","recall","f1-score"])
            for metric in macroavg_metrics.keys():
                macroavg_metrics[metric] = float(os.popen("cat " + results_filename + '| grep -P \"\\\"avg\_'+metric+': [0-9]\.[0-9]+\\\"\"' + '| grep -P -o \"[0-9]\.[0-9]+\"').read())

            macroavg_tech_metrics = dict.fromkeys(["accuracy","precision","recall","f1-score"])
            for metric in macroavg_tech_metrics.keys():
                macroavg_tech_metrics[metric] = float(os.popen("cat " + results_filename + '| grep -P \"\\\"avg\_tech\_'+metric+': [0-9]\.[0-9]+\\\"\"' + '| grep -P -o \"[0-9]\.[0-9]+\"').read())

            intensity_metrics = dict.fromkeys(["piano","mezzoforte","forte"])
            for intensity in intensity_metrics.keys():
                intensity_metrics[intensity] = dict.fromkeys(["accuracy","precision","recall","f1-score"])
                for metric in intensity_metrics[intensity].keys():
                    intensity_metrics[intensity][metric] = float(os.popen("cat " + results_filename + '| grep -P \"^'+intensity+"  "+metric+' [0-9]\.[0-9]+"' + '| grep -P -o \"[0-9]\.[0-9]+\"').read())

            # Delay
            adj_min = float(os.popen("cat " + results_filename + '| grep -P -o \"\\[ [0-9]+\\.[0-9]+\"| grep -P -o \"[0-9]+\\.[0-9]+\"').read())
            adj_max = float(os.popen("cat " + results_filename + '| grep -P -o \", [0-9]+\\.[0-9]+ \\]ms\"| grep -P -o \"[0-9]+\\.[0-9]+\"').read())
            avg = float(os.popen("cat " + results_filename +     '| grep -P -o \"avg_delay_glob:  \\d+\\.\\d+\"| grep -P -o \"\\d+\\.\\d+\"').read())
            perc = float(os.popen("cat " + results_filename +    '| grep -P -o \"[0-9]\\.[0-9]+  of the corr\"| grep -P -o \"[0-9]\\.[0-9]+\"').read())

            mavg_t_mean = float(os.popen("cat " + results_filename +    '| grep -P -o \"avg_tech_delay_mean: \\d+\\.\\d+\"| grep -P -o \"\\d+\\.\\d+\"').read())
            mavg_t_IQR = float(os.popen("cat " + results_filename +    '| grep -P -o \"avg_tech_delay_iqr: \\d+\\.\\d+\"| grep -P -o \"\\d+\\.\\d+\"').read())
            mavg_t_var = float(os.popen("cat " + results_filename +    '| grep -P -o \"avg_tech_delay_var: \\d+\\.\\d+\"| grep -P -o \"\\d+\\.\\d+\"').read())
            mavg_t_SD = float(os.popen("cat " + results_filename +    '| grep -P -o \"avg_tech_delay_sd: \\d+\\.\\d+\"| grep -P -o \"\\d+\\.\\d+\"').read())
            mavg_t_lofence = float(os.popen("cat " + results_filename +    '| grep -P -o \"avg_tech_lowfence: \\d+\\.\\d+\"| grep -P -o \"\\d+\\.\\d+\"').read())
            mavg_t_hifence = float(os.popen("cat " + results_filename +    '| grep -P -o \"avg_tech_highfence: \\d+\\.\\d+\"| grep -P -o \"\\d+\\.\\d+\"').read())
            mavg_t_percIn = float(os.popen("cat " + results_filename +    '| grep -P -o \"avg_tech_inrangeperc: \\d+\\.\\d+\"| grep -P -o \"\\d+\\.\\d+\"').read())

            relevant_metrics = {
                "glob_metrics":glob_metrics,
                "macroavg_metrics":macroavg_metrics,
                "macroavg_tech_metrics":macroavg_tech_metrics,
                "intensity_metrics":intensity_metrics,
                "mavg_t_mean":mavg_t_mean,
                "mavg_t_IQR":mavg_t_IQR,
                "mavg_t_var":mavg_t_var,
                "mavg_t_SD":mavg_t_SD,
                "mavg_t_lofence":mavg_t_lofence,
                "mavg_t_hifence":mavg_t_hifence,
                "mavg_t_percIn":mavg_t_percIn,
                "deprecated_delay":{
                    "adj_min":adj_min,
                    "adj_max":adj_max,
                    "avg":avg,
                    "perc":perc
                }
            }
            return relevant_info, relevant_metrics

        # If failsafe is True, the function avoids raising an error
        if failsafe:
            try:
                relevant_info = {
                    "onset_method":onset_method,
                    "buffer_size":buffer_size,
                    "hop_size":hop_size,
                    "minimum_inter_onset_interval_s":minimum_inter_onset_interval_s,
                    "silence_threshold":silence_threshold,
                    "onset_threshold":onset_threshold,
                    "results_filename":logres_filename
                }
                relevant_info, relevant_metrics = process_R_results(logres_filename)
            except:
                relevant_metrics = None
        else:
            relevant_info, relevant_metrics = process_R_results(logres_filename)
        if save_results is not True:
            os.system("rm -rf "+logres_filename)
        return relevant_info, relevant_metrics

def create_string(info,metrics,use_oldformat=False,do_copy = False,failsafe = True):
    if info:
        output_string = ""
        output_string += info["onset_method"]+"\t"
        output_string += str(info["buffer_size"])+"\t"
        output_string += str(info["hop_size"])+"\t"
        output_string += str(info["minimum_inter_onset_interval_s"])+"\t"
        output_string += str(info["silence_threshold"])+"\t"
        output_string += str(info["onset_threshold"])+"\t \t"
    if metrics:
        output_string += "{:.4f}".format(metrics["glob_metrics"]["accuracy"])+"\t"
        output_string += "{:.4f}".format(metrics["glob_metrics"]["precision"])+"\t"
        output_string += "{:.4f}".format(metrics["glob_metrics"]["recall"])+"\t"
        output_string += "{:.4f}".format(metrics["glob_metrics"]["f1-score"])+"\t"
        output_string += " \t"
        if use_oldformat:
            output_string += "{:.4f}".format(metrics["macroavg_metrics"]["accuracy"])+"\t"
            output_string += "{:.4f}".format(metrics["macroavg_metrics"]["precision"])+"\t"
            output_string += "{:.4f}".format(metrics["macroavg_metrics"]["recall"])+"\t"
            output_string += "{:.4f}".format(metrics["macroavg_metrics"]["f1-score"])+"\t"
            output_string += " \t"
        output_string += "{:.4f}".format(metrics["macroavg_tech_metrics"]["accuracy"])+"\t"
        output_string += "{:.4f}".format(metrics["macroavg_tech_metrics"]["precision"])+"\t"
        output_string += "{:.4f}".format(metrics["macroavg_tech_metrics"]["recall"])+"\t"
        output_string += "{:.4f}".format(metrics["macroavg_tech_metrics"]["f1-score"])+"\t"

        output_string += " \t"
        intensity_metrics=metrics["intensity_metrics"]
        for intensity in intensity_metrics.keys():
            for metric in intensity_metrics[intensity].keys():
                output_string += "{:.4f}".format(intensity_metrics[intensity][metric])+"\t"

        if use_oldformat:
            output_string += "{:.4f}".format(metrics["deprecated_delay"]["adj_min"])+"\t"
            output_string += "{:.4f}".format(metrics["deprecated_delay"]["avg"])+"\t"
            output_string += "{:.4f}".format(metrics["deprecated_delay"]["adj_max"])+"\t"
            output_string += "{:.4f}".format(metrics["deprecated_delay"]["perc"])+"\t"

        output_string += "{:.4f}".format(metrics["mavg_t_mean"])+"\t"
        output_string += "{:.4f}".format(metrics["mavg_t_IQR"])+"\t"
        output_string += "{:.4f}".format(metrics["mavg_t_var"])+"\t"
        output_string += "{:.4f}".format(metrics["mavg_t_SD"])+"\t"
        output_string += "{:.4f}".format(metrics["mavg_t_lofence"])+"\t"
        output_string += "{:.4f}".format(metrics["mavg_t_hifence"])+"\t"
        output_string += "{:.4f}".format(metrics["mavg_t_percIn"])+"\t"

        output_string += " \t"+info["results_filename"]
    if do_copy:
        import pyperclip
        pyperclip.copy(output_string)
        spam = pyperclip.paste()
    return output_string

def main():
    # *Main comparation hyperparameter*
    # This states the maximum time delay between labeled and detected onset
    # in order for them to be considered the same onset
    # Onsets further apart than this interval will be considered different
    MAX_ONSET_DIFFERENCE_S = 0.02
    print("Onset further apart than " + str(MAX_ONSET_DIFFERENCE_S*1000.0) + \
          "ms are considered different")

    # If true, consider as false positives all onsets detected before the label
    IGNORE_NEG = True

    # AUDIO_DIRECTORY = "compressed-audiofiles-soft-00"
    # AUDIO_DIRECTORY = "compressed-audiofiles-hard-02"
    # AUDIO_DIRECTORY = "gated-audiofiles-01"
    # AUDIO_DIRECTORY = "highpass-audiofiles-sum-2000-02"
    AUDIO_DIRECTORY = "audiofiles"

    # AUBIOONSET_COMMAND = "utility_scripts/customAubio/aubioonset-mkl-nowhitening"
    AUBIOONSET_COMMAND = "aubioonset"

    print("\nAudio from folder \""+AUDIO_DIRECTORY+"\"\n")
    print("Aubio command: \""+AUBIOONSET_COMMAND+"\"\n")

    READ_BUFFERSIZE = -1
    READ_SILENCE = ""
    READ_THRESH = ""
    READ_METHOD = ""
    if len(sys.argv) == 2:
        READ_METHOD = sys.argv[1]
    elif len(sys.argv) == 3:
        READ_METHOD = sys.argv[1]
        READ_BUFFERSIZE = sys.argv[2]
    elif len(sys.argv) == 4:
        READ_METHOD = sys.argv[1]
        READ_BUFFERSIZE = sys.argv[2]
        READ_SILENCE = sys.argv[3]
    elif len(sys.argv) == 5:
        READ_METHOD = sys.argv[1]
        READ_BUFFERSIZE = sys.argv[2]
        READ_SILENCE = sys.argv[3]
        READ_THRESH = sys.argv[4]
    elif len(sys.argv) > 5:
        print("Too many arguments")
        exit(-1)

    class ParamType(Enum):  # Aubioonset parameter type
        INT = 1
        FLOAT = 2
        STR = 3

    # Ask the user to input the parameter, or use default if none is specified
    def readParam(param_name,default_value,param_type):
        try:
            param_str = input(param_name+"(default: " + str(default_value) + "): ")
            if param_str != "":
                if param_type is ParamType.INT:
                    param_val = int(param_str)
                elif param_type is ParamType.FLOAT:
                    param_val = float(param_str)
                elif param_type is ParamType.STR:
                    param_val = param_str
                else:
                    print("ERROR! Wrong parameter type")
                    exit()
            else:
                param_val = default_value;
                print("Using default value for " + param_name + " (" + str(default_value) + ")")
            return param_val
        except ValueError:
            print("ValueError")

    # Read all the parameters
    print("Extracting all the onsets from the wav files in this folder")
    print("Specify the parameter values or press <ENTER> for default")
    if READ_BUFFERSIZE == -1:
        BUFFER_SIZE = readParam("BUFFER_SIZE",64,ParamType.INT)
    else:
        BUFFER_SIZE = READ_BUFFERSIZE
    HOP_SIZE = 64#readParam("HOP_SIZE",64,ParamType.INT)
    if READ_SILENCE == "":
        SILENCE_THRESHOLD = readParam("SILENCE_THRESHOLD",-48.0,ParamType.FLOAT)
    else:
        SILENCE_THRESHOLD = READ_SILENCE
    if READ_THRESH == "":
        ONSET_THRESHOLD = readParam("ONSET_THRESHOLD",0.75,ParamType.FLOAT)
    else:
        ONSET_THRESHOLD = READ_THRESH
    if READ_METHOD == "":
        print("Available methods:<default|energy|hfc|complex|phase|specdiff|kl|mkl|specflux>")
        ONSET_METHOD = readParam("ONSET_METHOD","hfc",ParamType.STR)
    else:
        ONSET_METHOD = READ_METHOD
    MINIMUM_INTER_ONSET_INTERVAL_SECONDS = 0.020 #readParam("MINIMUM_INTER_ONSET_INTERVAL_SECONDS",0.020,ParamType.FLOAT)

    relevant_info, relevant_metrics = perform_main_analysis(AUDIO_DIRECTORY,AUBIOONSET_COMMAND,ONSET_METHOD,BUFFER_SIZE,HOP_SIZE,SILENCE_THRESHOLD,ONSET_THRESHOLD,MINIMUM_INTER_ONSET_INTERVAL_SECONDS,MAX_ONSET_DIFFERENCE_S,IGNORE_NEG)
    print(create_string(relevant_info,relevant_metrics, do_copy=True))

if __name__ == "__main__":
    main()
