### Voting analysis project ###
require(corrplot)
require(ggplot2)
require(reshape2)
require(plyr)

# load precinct data
filepath<- "/Users/lisarayle/Dropbox/sf_data/elections/"
filename<-"voting_data_all_11052016.csv"
df <- read.csv(paste(filepath,filename,sep=""))
#df <- na.omit(df)

# load table of election results 
filename<-"BallotPropositions_nimby2.csv"
results <- read.csv(paste(filepath, filename, sep=""))
results.short <- results[,c(5,15)]

# merge NimybyWin (outcome) column onto df. 
df <- merge(df, results.short, by.x="yr_prop",by.y="Prop.ID", all.x=TRUE)

hist(df$pct_nimby)
#pairs(pct_nimby~owned+med_inc_adj+med_val_adj,data=df, main="Simple Scatterplot Matrix")

df$pop_dens = df$tot_pop/df$area_m
#### Correlation plots, etc. ####

# corr plot with selected columns
# don't include foreign_born because there are a lot of NAs
#cols <- c("pct_nimby","asian","black","families","hispanic","hu_detatched","med_age","med_inc_adj","med_val_adj","med_hu_age","med_yrs_lived","med_yrs_lived_owner","owned","white","turnout")
# columns <- "NO","YES","area_m","asian","black","families","foreign_born","hispanic","hu_10.19","hu_20.49","hu_2","hu_3.4","hu_5.9","hu_50","hu_detatched","med_age","med_inc_adj","med_val_adj","med_yr_built","med_yr_moved_all","med_yr_moved_owner","nov_elec","occ_hu","owned","pct_nimby","precname","pres_elec","rented","tot_hhs","tot_hu","tot_nimby_votes","tot_pop","voted","white","yr_1996","yr_1997","yr_1998","yr_1999","yr_2000","yr_2001","yr_2002","yr_2004","yr_2006","yr_2008","yr_2013","yr_2014","yr_2015"
#cols <- c("pct_nimby","med_age","med_inc_adj","med_val_adj","med_yr_built")
#M<- df[,cols]
#M <- na.omit(M)
#cor.M <- cor(M)
#corrplot(cor.M, method="ellipse")

vars <- c("pct_nimby","black","families","hispanic","hu_detatched","med_age","med_inc_adj","med_val_adj","med_hu_age","med_yrs_lived","med_yrs_lived_owner","owned","white","pres_elec","turnout")
yr.dummies <-c("yr_1996","yr_1997","yr_1998","yr_1999","yr_2000","yr_2001","yr_2002","yr_2004","yr_2006","yr_2008","yr_2013","yr_2014","yr_2015")
#### try some regressions ####

#fit.1 <- lm(pct_nimby~black+hispanic+white+families+hu_detatched+med_age+med_inc_adj+med_val_adj+med_hu_age+med_yrs_lived+med_yrs_lived_owner+rented+pop_dens+pres_elec+turnout, data=df)
#summary(fit.1)

# added in asian. removed med_yr_moved_all
#fit.2 <- lm(pct_nimby~asian+black+white+hispanic+families+hu_detatched+med_age+med_inc_adj+med_val_adj+med_yrs_lived_owner+owned+pop_dens+pres_elec+turnout, data=df)
#summary(fit.2)

# removed hu_detached
#fit.3 <- lm(pct_nimby~asian+black+hispanic+white+families+med_age+med_inc_adj+med_val_adj+med_hu_age+med_yrs_lived_owner+rented+pop_dens+pres_elec+turnout, data=df)
#summary(fit.3)

# add in year dummies
fit.4 <- lm(pct_nimby~asian+black+hispanic+white+med_age+med_inc_adj+med_val_adj+med_hu_age+med_yrs_lived_owner+owned+pop_dens+pres_elec+turnout+yr_1996+yr_1997+yr_1998+yr_1999+yr_2000+yr_2001+yr_2002+yr_2004+yr_2006+yr_2008+yr_2013+yr_2014+yr_2015, data=df)
summary(fit.4)

# what happens when do it with just one year? 

df.1999<- subset(df, yr_1999=="True")
fit.1999 <-lm(pct_nimby~asian+black+hispanic+white+families+med_age+med_inc_adj+med_val_adj+med_hu_age+med_yrs_lived_owner+rented+pop_dens+turnout, data=df.1999)
summary(fit.1999)


df.2014<- subset(df, yr_2014=="True")
fit.2014 <-lm(pct_nimby~asian+black+hispanic+white+families+med_age+med_inc_adj+med_val_adj+med_hu_age+med_yrs_lived_owner+rented+pop_dens+turnout, data=df.2014)
summary(fit.2014)

# Nov 4: I added a turnout variable, which slightly improves the model, but only a little bit. 
# It has a plausible sign though: negative. 

# I'm curious how many people actully vote yes or no, as a percent of total residents. 
df$pct_totres<- df$voted/df$tot_pop
summary(df$pct_totres)
# On average, 11.3% of residents vote for nimby stuff. 

# pct nimby over time? 

plot(df$year, df$pct_nimby)
boxplot(df$pct_nimby~df$year)
# No clear pattern.

# What if we break it down for certain ballot measures? Are there some that are clearly outliers? 
# keep in mind these are distributions for precincts, not the actual individual votes. 
boxplot(df$pct_nimby~df$yr_prop)
remappings=c("199603B"="96 B", "199706F"="97 F", "199711H"="H", "199806E"="98 E", "199806I"="I", "199806K"="K", "199811E"="E", "199911H"="99 H", "199911I"="I", "199911J"="J", "200003C"="00 C", "200011K"="K", "200011L"="L", "200111D"="01 D", "200203D"="02 D", "200211B"="B", "200211R"="R", "200403J"="04 J", "200411A"="A", "200611G"="06 G", "200806F"="08 F", "200806G"="G", "201311B"="13 B", "201311C"="C", "201406B"="14 B", "201411F"="F", "201511D"="15 D", "201511I"="I")
p<- ggplot(df, aes(x=yr_prop, y=pct_nimby))
mytheme<-theme(text = element_text(size=20),axis.text.x = element_text(angle=45, hjust=1))
p+geom_violin()+scale_x_discrete("Election", labels = remappings)+mytheme

#### Filter for only very nimby measures ####
#try excluding the elections where it's not clear whether it's really a nimby issue.
# So exclude the "Maybe"s
# here are the props to exclude: 199811E, 199911J, 200003C, 200211B, 200211R, 200411A
to.exclude = with(results, Prop.ID[Maybe.Nimby.=="Maybe"])
df.filtered<-df[!(df$yr_prop %in% to.exclude),]

# try model again with filtered dataset
fit.4 <- lm(pct_nimby~asian+black+hispanic+white+med_age+med_inc_adj+med_val_adj+med_hu_age+med_yrs_lived_owner+owned+pop_dens+pres_elec+turnout+yr_1996+yr_1997+yr_1998+yr_1999+yr_2001+yr_2002+yr_2004+yr_2006+yr_2008+yr_2013+yr_2014, data=df.filtered)
summary(fit.4)
# WAY better fit!!

# trying removing some variables that aren't significant. Removed med_age and med_hu_age, med_val_adj, med_inc_adj+med_yrs_lived_owner+. 
fit.5 <- lm(pct_nimby~asian+black+hispanic+white+owned+pop_dens+pres_elec+turnout+yr_1996+yr_1997+yr_1998+yr_1999+yr_2001+yr_2002+yr_2004+yr_2006+yr_2008+yr_2013+yr_2014, data=df.filtered)
summary(fit.5)
# removing those variables did not reduce the explanatory power at all. 

# fixed 2002 data, so that's fine

# try putting back in some other variables: hu_50 
# This is best model so far.
fit.6 <- lm(pct_nimby~asian+black+hispanic+white+owned+hu_50+pop_dens+pres_elec+turnout+yr_1996+yr_1997+yr_1998+yr_1999+yr_2001+yr_2002+yr_2004+yr_2006+yr_2008+yr_2013+yr_2014, data=df.filtered)
summary(fit.6)
# hu_50 is significant! 


boxplot(df$pct_nimby~df$yr_prop)

p<- ggplot(df.filtered, aes(x=yr_prop, y=pct_nimby))
p+geom_violin()+scale_x_discrete("Election", labels = remappings)+mytheme


summary(df.filtered$pct_totres)


p<- ggplot(df.filtered, aes(x=yr_prop, y=turnout))
p<-p+geom_violin(aes(fill=NimbyWin))+scale_x_discrete("Election", labels = remappings)+scale_y_continuous(limits = c(0,1))+mytheme
p<-p+geom_hline(yintercept=mean(df.filtered$turnout, na.rm = TRUE))
show(p)

nimby.by.elec <- aggregate(pct_nimby~yr_prop, df.filtered, FUN=mean)
turnout.by.elec <- aggregate(turnout~yr_prop, df.filtered, FUN=mean)
var.by.elec <- aggregate(cbind(pct_nimby,turnout)~yr_prop, df.filtered, FUN=mean)

dm<-melt(var.by.elec)
p<- ggplot(dm, aes(x=yr_prop,value, colour=variable))
p+geom_point(size=3)+scale_x_discrete("Election", labels = remappings)+mytheme+scale_y_continuous(limits = c(0,1))

# I think maybe the relationships are changing over time... 
for(yr in sort(unique(df.filtered$yr_prop))){
  df.sub <- subset(df,yr_prop==yr)
  p<- ggplot(df.sub, aes(x=med_inc_adj, y=pct_nimby))
  p<-p+geom_point(colour='blue', alpha=.2)+labs(title=paste("Elections in",yr))
  show(p)
}

