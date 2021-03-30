#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

if(length(args) != 1)
  quit()

DO_PLOT <- FALSE
SAVEPLOT <- FALSE
SHOWPLOT <- FALSE

if(!SAVEPLOT && SHOWPLOT){
  library(tcltk)
}
CSV_PATH <- args[1]

# dir = (tail(unlist(strsplit(getwd(),"/")),1))
# CSV_PATH=""
# if(dir == "r_analysis"){
#   CSV_PATH = "../../output/onset_delay.csv"
# }else if(dir == "src"){
#   CSV_PATH = "output/onset_delay.csv"
# }else{
#   print("Call from a project directory")
#   exit()
# }
onsets = read.csv(CSV_PATH, na.strings = "NAN")


total = nrow(onsets)
true_predictions = length(na.omit(onsets$difference))
FP = sum(is.na(onsets$onset_labeled))
FN = sum(is.na(onsets$onset_extracted))
# Sanity checks
stopifnot(FP+FN == total - true_predictions)

sprintf("%d  onsets were labeled",length(na.omit(onsets$onset_labeled)))

accuracy = true_predictions / total
sprintf("accuracy: %.10f",accuracy)

precision = true_predictions / (true_predictions + FP)
recall    = true_predictions / (true_predictions + FN)


sprintf("precision: %.10f",precision)
sprintf("recall: %.10f",recall)
f1    = 2.0 * ((precision*recall)/(precision+recall))

sprintf("f1-score: %.10f",f1)


print("Delay summary (in ms)")
delays_ms = na.omit(onsets$difference)*1000
summary(delays_ms)
sprintf("avg_delay_glob:  %.10f",mean(delays_ms))
sprintf("iqr_delay_glob:  %.10f",IQR(delays_ms))
sprintf("var_delay_glob:  %.10f",var(delays_ms))
sprintf("sd_delay_glob:  %.10f",sd(delays_ms))



print("Per Sound type")
soundtype_name <- c("percussive","pitched")
soundtype_pattern <- c("_percussive_", "_pitched_")

accuracies = c()
precisions = c()
recalls = c()
f1s = c()

delay_means = c()
delay_iqrs = c()
delay_vars = c()
delay_sds = c()

for(i in 1:length(soundtype_name)){
  difference_temp = onsets$difference[grepl(soundtype_pattern[i],onsets$recording)]
  onset_labeled_temp = onsets$onset_labeled[grepl(soundtype_pattern[i],onsets$recording)]
  onset_extracted_temp = onsets$onset_extracted[grepl(soundtype_pattern[i],onsets$recording)]

  accuracy_temp <- length(na.omit(difference_temp)) / length(difference_temp)
  FP_temp = sum(is.na(onset_labeled_temp))
  FN_temp = sum(is.na(onset_extracted_temp))
  true_predictions_temp=length(na.omit(difference_temp))
  precision_temp <- true_predictions_temp / (true_predictions_temp + FP_temp)
  recall_temp <- true_predictions_temp / (true_predictions_temp + FN_temp)
  f1_tmp <- 2.0 * ((precision_temp*recall_temp)/(precision_temp+recall_temp))

  print("")
  print(soundtype_name[i])
  print(paste(length(na.omit(onset_labeled_temp))," ",soundtype_name[i]," onsets were labeled"))
  cat(sprintf("%s  accuracy %.10f\n",soundtype_name[i],accuracy_temp))
  cat(sprintf("%s  precision %.10f\n",soundtype_name[i],precision_temp))
  cat(sprintf("%s  recall %.10f\n",soundtype_name[i],recall_temp))
  cat(sprintf("%s  f1-score %.10f\n",soundtype_name[i],f1_tmp))

  accuracies[i] <- accuracy_temp
  precisions[i] <- precision_temp
  recalls[i] <- recall_temp
  f1s[i] <- f1_tmp

  prefix = soundtype_name[i]
  cat(sprintf("Delay summary (in ms)\n"))
  temp_delays_ms = na.omit(difference_temp)*1000
  temp_summary = summary(temp_delays_ms)
  temp_lab = c("Min","1st_Qu","Median","Mean","3rd_Qu","Max")
  for(j in 1:length(temp_lab)){
    cat(sprintf("%s: %.2f ",temp_lab[j],temp_summary[j]))
  }
  cat(sprintf("\n"))
  delay_means[i] <- mean(temp_delays_ms)
  delay_iqrs[i] <- IQR(temp_delays_ms)
  delay_vars[i] <- var(temp_delays_ms)
  delay_sds[i] <- sd(temp_delays_ms)
  cat(sprintf("%s  avg_delay:  %.10f\n",prefix,delay_means[i]))
  cat(sprintf("%s  iqr_delay:  %.10f\n",prefix,delay_iqrs[i]))
  cat(sprintf("%s  var_delay:  %.10f\n",prefix,delay_vars[i]))
  cat(sprintf("%s  sd_delay:  %.10f\n",prefix,delay_sds[i]))
}

print("Average metrics per soundtype")
sprintf("avg_accuracy: %.10f",mean(accuracies))
sprintf("avg_precision: %.10f",mean(precisions))
sprintf("avg_recall: %.10f",mean(recalls))
sprintf("avg_f1-score: %.10f",mean(f1s))


sprintf("avg_delay_mean: %.10f",mean(delay_means))
sprintf("avg_delay_iqr: %.10f",mean(delay_iqrs))
sprintf("avg_delay_var: %.10f",mean(delay_vars))
sprintf("avg_delay_sd: %.10f",mean(delay_sds))











print("Per Intensity metrics")
intensities_name <- c("piano","mezzoforte","forte")
intensities_pattern <- c("_p_", "_mf_", "_f_")

for(i in 1:length(intensities_name)){
  difference_temp = onsets$difference[grepl(intensities_pattern[i],onsets$recording)]
  onset_labeled_temp = onsets$onset_labeled[grepl(intensities_pattern[i],onsets$recording)]
  onset_extracted_temp = onsets$onset_extracted[grepl(intensities_pattern[i],onsets$recording)]

  accuracy_temp <- length(na.omit(difference_temp)) / length(difference_temp)
  FP_temp = sum(is.na(onset_labeled_temp))
  FN_temp = sum(is.na(onset_extracted_temp))
  true_predictions_temp=length(na.omit(difference_temp))
  precision_temp <- true_predictions_temp / (true_predictions_temp + FP_temp)
  recall_temp <- true_predictions_temp / (true_predictions_temp + FN_temp)
  f1_tmp <- 2.0 * ((precision_temp*recall_temp)/(precision_temp+recall_temp))

  print("")
  print(intensities_name[i])
  cat(sprintf("%s  accuracy %.10f\n",intensities_name[i],accuracy_temp))
  cat(sprintf("%s  precision %.10f\n",intensities_name[i],precision_temp))
  cat(sprintf("%s  recall %.10f\n",intensities_name[i],recall_temp))
  cat(sprintf("%s  f1-score %.10f\n",intensities_name[i],f1_tmp))
}




print("Per Technique")
technique_name <- c("keybed", "kick","lowerside","thumb","palmmute","naturalharmonics","picknearbridge","soundhole")
technique_pattern <- c("keybed", "kick","lowerside","thumb","palmmute","naturalharmonics","picknearbridge","soundhole")

accuracies_by_technique = c()
precisions_by_technique = c()
recalls_by_technique = c()
f1s_by_technique = c()

delay_means_by_technique <- c()
delay_iqrs_by_technique <- c()
delay_vars_by_technique <- c()
delay_sds_by_technique <- c()

delay_lower_fences_by_technique <- c()
delay_upper_fences_by_technique <- c()
delay_inrange_percentage_by_technique <- c()

for(i in 1:length(technique_name)){
  difference_temp = onsets$difference[grepl(technique_pattern[i],onsets$recording)]
  onset_labeled_temp = onsets$onset_labeled[grepl(technique_pattern[i],onsets$recording)]
  onset_extracted_temp = onsets$onset_extracted[grepl(technique_pattern[i],onsets$recording)]

  accuracy_temp <- length(na.omit(difference_temp)) / length(difference_temp)
  FP_temp = sum(is.na(onset_labeled_temp))
  FN_temp = sum(is.na(onset_extracted_temp))
  true_predictions_temp=length(na.omit(difference_temp))
  precision_temp <- true_predictions_temp / (true_predictions_temp + FP_temp)
  recall_temp <- true_predictions_temp / (true_predictions_temp + FN_temp)
  f1_tmp <- 2.0 * ((precision_temp*recall_temp)/(precision_temp+recall_temp))

  print("")
  print(paste("Technique: ",technique_name[i]))
  print(paste(length(na.omit(onset_labeled_temp))," ",technique_name[i]," onsets were labeled"))
  cat(sprintf("%s  accuracy %.10f\n",technique_name[i],accuracy_temp))
  cat(sprintf("%s  precision %.10f\n",technique_name[i],precision_temp))
  cat(sprintf("%s  recall %.10f\n",technique_name[i],recall_temp))
  cat(sprintf("%s  f1-score %.10f\n",technique_name[i],f1_tmp))

  accuracies_by_technique[i] <- accuracy_temp
  precisions_by_technique[i] <- precision_temp
  recalls_by_technique[i] <- recall_temp
  f1s_by_technique[i] <- f1_tmp


  prefix = technique_name[i]
  cat(sprintf("Delay summary (in ms)\n"))
  temp_delays_ms = na.omit(difference_temp)*1000
  temp_summary = summary(temp_delays_ms)
  temp_lab = c("Min","1st_Qu","Median","Mean","3rd_Qu","Max")
  for(j in 1:length(temp_lab)){
    cat(sprintf("%s: %.2f ",temp_lab[j],temp_summary[j]))
  }
  cat(sprintf("\n"))
  delay_means_by_technique[i] <- mean(temp_delays_ms)
  delay_iqrs_by_technique[i] <- IQR(temp_delays_ms)
  delay_vars_by_technique[i] <- var(temp_delays_ms)
  delay_sds_by_technique[i] <- sd(temp_delays_ms)
  cat(sprintf("%s  avg_delay:  %.10f\n",prefix,delay_means_by_technique[i]))
  cat(sprintf("%s  iqr_delay:  %.10f\n",prefix,delay_iqrs_by_technique[i]))
  cat(sprintf("%s  var_delay:  %.10f\n",prefix,delay_vars_by_technique[i]))
  cat(sprintf("%s  sd_delay:  %.10f\n",prefix,delay_sds_by_technique[i]))

  k = 1.5
  delay_lower_fences_by_technique[i] <- quantile(temp_delays_ms,0.25) - (k *delay_iqrs_by_technique[i])
  delay_upper_fences_by_technique[i] <- quantile(temp_delays_ms,0.75) + (k *delay_iqrs_by_technique[i])

  cat(sprintf("%s  lower_fence:  %.10f\n",prefix,delay_lower_fences_by_technique[i]))
  cat(sprintf("%s  upper_fence:  %.10f\n",prefix,delay_upper_fences_by_technique[i]))
  delay_inrange_percentage_by_technique[i] = 0
  tmpperc = 0
  for(onsetdiff in na.omit(temp_delays_ms)){
    if(onsetdiff < delay_upper_fences_by_technique[i] && onsetdiff > delay_lower_fences_by_technique[i]){
      tmpperc <- tmpperc + 1
    }
  }
  delay_inrange_percentage_by_technique[i] <- tmpperc/length(na.omit(temp_delays_ms))
}

print("Average metrics per technique")
sprintf("avg_tech_accuracy: %.10f",mean(accuracies_by_technique))
sprintf("avg_tech_precision: %.10f",mean(precisions_by_technique))
sprintf("avg_tech_recall: %.10f",mean(recalls_by_technique))
sprintf("avg_tech_f1-score: %.10f",mean(f1s_by_technique))

sprintf("avg_tech_delay_mean: %.10f",mean(delay_means_by_technique))
sprintf("avg_tech_delay_iqr: %.10f",mean(delay_iqrs_by_technique))
sprintf("avg_tech_delay_var: %.10f",mean(delay_vars_by_technique))
sprintf("avg_tech_delay_sd: %.10f",mean(delay_sds_by_technique))


sprintf("avg_tech_lowfence: %.10f",mean(delay_lower_fences_by_technique))
sprintf("avg_tech_highfence: %.10f",mean(delay_upper_fences_by_technique))
sprintf("avg_tech_inrangeperc: %.10f",mean(delay_inrange_percentage_by_technique))








if(SAVEPLOT){
  pdf(file = "./delay.pdf",   # The directory you want to save the file in
      width = 5, # The width of the plot in inches
      height = 8) # The height of the plot in inches
}else if (SHOWPLOT) {
  x11()
  prompt  <- "Close plot?"
  extra   <- ""
}

lower_adj <- 0.001
upper_adj <- 0.001
percentage <- 0.001
if (DO_PLOT)
{
  bp = boxplot(delays_ms,main="Onset Detection Delay (ms)",ylab="Delay(ms)", ylim=c(0.0,20.0), yaxt="n")
  axis(2, at=seq(0, 20, by=1),las=1)
  lower_adj = bp$stats[1]
  upper_adj = bp$stats[5]
  sprintf("adjacent min-max:  %.10f   %.10f",lower_adj,upper_adj)
  percentage = 0
  for(onsetdiff in na.omit(onsets$difference)){
    if(onsetdiff*1000 < upper_adj && onsetdiff*1000 > lower_adj){
      percentage = percentage + 1
    }
  }
  percentage = percentage/length(na.omit(onsets$difference))
}
print(paste(percentage," of the correctly detected onsets fall in the range [",lower_adj,",",upper_adj,"]ms"))

if(SAVEPLOT){
  dev.off()
}else if (SHOWPLOT) {
  capture <- tk_messageBox(message = prompt, detail = extra)
}


if(SAVEPLOT){
  pdf(file = "./metrics.pdf",   # The directory you want to save the file in
      width = 6, # The width of the plot in inches
      height = 8) # The height of the plot in inches
}

if (DO_PLOT)
{
  metrics <- c(c(accuracy,precision,recall))
  bx <- barplot(metrics,
                names.arg = c("Accuracy","Precision","Recall"),
                ylim=c(0,1))
  
  text(bx,metrics*.9,labels = format(round(metrics, 4), nsmall = 4))
}
if(SAVEPLOT){
  dev.off()
}else if (SHOWPLOT) {
  capture <- tk_messageBox(message = prompt, detail = extra)
}

