library(ggplot2)
library(reshape)
library(forecast)

# Note that generating these plots takes about 15 minutes.

temp = list.files(path="../generated/historical-data/csv/", pattern="*.csv")

for (i in 1:length(temp)) {
    df<-read.csv(file=paste("../generated/historical-data/csv/", temp[i], sep=""),header=TRUE,sep=";")
    df$date = as.POSIXct(as.numeric(as.character(df$date)),origin="1970-01-01",tz="GMT")
    g <- ggplot() + 
        geom_line(data=df, aes(x=date, y=nr_builtins)) + expand_limits(y=0) +
        geom_point(data=df, aes(x=date, y=nr_builtins), color="red", size=1.2) +
        theme(panel.grid.minor = element_blank(), panel.background = element_blank(), axis.line = element_line(colour = "black"), axis.text = element_text(size = 7), axis.title = element_text(size = 9))
        #geom_line(data=timeseries, color="red")
    ggsave(filename=paste("../generated/historical-data/plots/png/", temp[i], ".png", sep=""), plot=g, width=20, height=8, units="cm")
    ggsave(filename=paste("../generated/historical-data/plots/pdf/", temp[i], ".pdf", sep=""), plot=g, width=8.45, height=3, units="cm")
}
