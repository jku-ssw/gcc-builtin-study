# Plot Figure 4 (builtin development illustrated on four representative projects)

library(ggplot2)
library(reshape)
library(forecast)

    
df1<-read.csv(file="../generated/historical-data/csv/4740-intel-tinycbor.csv",header=TRUE,sep=";")
df1$project <- "tinycbor"
df2<-read.csv(file="../generated/historical-data/csv/252-sheepdog-sheepdog.csv",header=TRUE,sep=";")
df2$project <- "sheepdog"
df3<-read.csv(file="../generated/historical-data/csv/5-libav-libav.csv",header=TRUE,sep=";")
df3$project <- "libav"
df4<-read.csv(file="../generated/historical-data/csv/761-vstakhov-libucl.csv",header=TRUE,sep=";")
df4$project <- "libucl"
df <- rbind(df1, df2, df3, df4)
df$project <- factor(df$project, c("libucl", "libav", "tinycbor", "sheepdog"))

df$date = as.POSIXct(as.numeric(as.character(df$date)),origin="1970-01-01",tz="GMT")
g <- ggplot() + 
    geom_line(data=df, aes(x=date, y=nr_builtins)) + expand_limits(y=0) +
    geom_point(data=df, aes(x=date, y=nr_builtins), color="red", size=1) +
    theme(plot.margin = unit(c(-0.1,0.1,0.1,0.1), "cm"), panel.grid.minor = element_blank(), panel.background = element_blank(), axis.line = element_line(colour = "black"), axis.text = element_text(size = 5), axis.title = element_text(size = 7), strip.text = element_text(size = 7), strip.background = element_blank()) +
    facet_wrap(~ project, scales="free", nrow=1)
ggsave(filename="../generated/plots/fourplots.pdf", plot=g, width=16.9, height=2.5, units="cm")
