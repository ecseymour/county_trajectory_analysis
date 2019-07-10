# final script for JGeogSyst paper

# 1. create sequences separately for growing and shrinking counties 2000-2010
# 2. create dissimilarity matrices using OMspell
# 3. cluster data using wards linkage
# 4. generate plots for sequencess in each cluster

# load libraries
library(TraMineR)
library(cluster)
library(WeightedCluster)
library(plyr)
library(extrafont)

loadfonts(device = "postscript") ## for postscript()

##################################
##################################
# loss data
##################################
##################################
# import data
mydata <- read.csv('../output/vars_for_traminer_loss.csv', header = TRUE,
                   sep = ",", colClasses = c(replicate(7, 'character')))
# mydata <- rename(mydata, replace = c("X60"="1960", "X70"="1970", "X80"="1980", "X90"="1990", "X00"="2000", "X10"="2010"))
names(mydata) <- gsub("X", "", names(mydata))
# use FIPS as row name
row.names(mydata) <- mydata$geoid10
# remove fips as col in dataframe
mydata$geoid10 <- NULL
# create state sequence labels
mydata.lab <- c("SL, NL", "SL, NG", "SG, NL", "SG, NG")
mydata.lab <- c("Self Loss, Neighbor Loss", "Self Loss, Neighbor Growth", "Self Growth, Neighbor Loss", "Self Growth, Neighbor Growth")
# create state sequence object
mydata.seq <- seqdef(mydata, 1:6, xstep=4, labels = mydata.lab)
######
# sequence frequency plots

# analyze state and trajectory frequency
w <- 6
h <- w / 1.618


setEPS()
postscript(file = "../output/lossStateDistributionPlot.eps",
    width = w, height = h)
seqdplot(mydata.seq, border = NA, with.legend = "right", legend.prop = 0.3)
dev.off()


setEPS()
postscript(file = "../output/lossSequencIndexPlot.eps",
    width = w, height = h)
seqIplot(mydata.seq, with.legend = "right", legend.prop = 0.3)
dev.off()

#####
# cluster data

# generate sm and indel costs
costs.tr <- seqcost(mydata.seq, method = "TRATE", with.missing = FALSE)
# calc distances using OM sequence of spells 
mydata.OMspell <- seqdist(mydata.seq, method = "OMspell",
                          sm = costs.tr$sm, indel = costs.tr$indel, 
                          expcost = 1, tpow = 1.5)
# cluster data using ward's linkage
clusterward <- hclust(as.dist(mydata.OMspell), method = "ward.D2")
# retain four clusters
myK <- 4
mydata.cut <- cutree(clusterward, k = myK)
# generate labels for clusters
# cut.lab <- factor(mydata.cut, labels = paste("Cluster", 1:myK))

# relabel using cluster number for backward compatability with older code
cut.lab <- factor(mydata.cut, labels = c('Emerging Loss', 'Punctuated Loss', 'Persistent Loss', 'Isolated Loss'))
cl4.lab <- factor(mydata.cut, labels = paste("Cluster", 1:4))
write.csv(cbind(mydata, cl4.lab), file="../output/TraMineR_loss_omspell.csv")

setEPS()
postscript(file = "../output/lossClustersSequencePlots.eps",
    width = w, height = h * 1.681)
seqIplot(mydata.seq, group = cut.lab, border = NA, with.legend = TRUE, 
         sortv="from.end", legend.prop = 0.1, cpal=c('#1f78b4', '#a6cee3', '#b2df8a', '#33a02c' ))
dev.off()

##################################
##################################
# growth data
##################################
##################################
# import data
mydata <- read.csv('../output/vars_for_traminer_growth.csv', header = TRUE,
                   sep = ",", colClasses = c(replicate(7, 'character')))
# mydata <- rename(mydata, replace = c("X60"="1960", "X70"="1970", "X80"="1980", "X90"="1990", "X00"="2000", "X10"="2010"))
names(mydata) <- gsub("X", "", names(mydata))
# use FIPS as row name
row.names(mydata) <- mydata$geoid10
# remove fips as col in dataframe
mydata$geoid10 <- NULL
# create state sequence labels
# mydata.lab <- c("SL, NL", "SL, NG", "SG, NL", "SG, NG")
mydata.lab <- c("Self Loss, Neighbor Loss", "Self Loss, Neighbor Growth", "Self Growth, Neighbor Loss", "Self Growth, Neighbor Growth")
# create state sequence object
mydata.seq <- seqdef(mydata, 1:6, xstep=4, labels = mydata.lab)

######
# sequence frequency plots

# analyze state and trajectory frequency
w <- 6
h <- w / 1.618


setEPS()
postscript(file = "../output/growthStateDistributionPlot.eps",
    width = w, height = h)
seqdplot(mydata.seq, border = NA, with.legend = "right", legend.prop = 0.3)
dev.off()


setEPS()
postscript(file = "../output/growthSequencIndexPlot.eps",
    width = w, height = h)
seqIplot(mydata.seq, with.legend = "right", legend.prop = 0.3)
dev.off()


#####
# cluster data

# generate sm and indel costs
costs.tr <- seqcost(mydata.seq, method = "TRATE", with.missing = FALSE)
# calc distances using OM sequence of spells 
mydata.OMspell <- seqdist(mydata.seq, method = "OMspell",
                          sm = costs.tr$sm, indel = costs.tr$indel, 
                          expcost = 1, tpow = 1.5)
# cluster data using ward's linkage
clusterward <- hclust(as.dist(mydata.OMspell), method = "ward.D2")
# retain four clusters
myK <- 4
mydata.cut <- cutree(clusterward, k = myK)
# generate labels for clusters
cut.lab <- factor(mydata.cut, labels = c('Early Recovery', 'Constant Growth', 'Intermittent Growth', 'Interrupted Growth'))
cl4.lab <- factor(mydata.cut, labels = paste("Cluster", 1:4))
write.csv(cbind(mydata, cl4.lab), file="../output/TraMineR_growth_omspell.csv")

setEPS()
postscript(file = "../output/growthClustersSequencePlots.eps",
    width = w, height = h * 1.681)
seqIplot(mydata.seq, group = cut.lab, border = NA, with.legend = TRUE, 
         sortv="from.end", legend.prop = 0.1, cpal=c('#1f78b4', '#a6cee3', '#b2df8a', '#33a02c' ))
dev.off()
