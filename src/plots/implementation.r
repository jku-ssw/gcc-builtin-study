# Plots Figure 3 (the implementation effort evaluated using a greedy and frequency-based strategy)

library(ggplot2)
library(scales)

greedy_libc<-read.csv(file="../generated/greedy-all.csv",header=TRUE,sep=";")
greedy_libc$name<-"greedy"
greedy_nolibc<-read.csv(file="../generated/greedy-machine-independent.csv",header=TRUE,sep=";")
greedy_nolibc$name<-"greedy \n (machine-independent)"
most_frequent<-read.csv(file="../generated/most-frequent-all.csv",header=TRUE,sep=";")
most_frequent$name<-"frequency"
most_frequent_nolibc<-read.csv(file="../generated/most-frequent-machine-independent.csv",header=TRUE,sep=";")
most_frequent_nolibc$name<-"frequency\n(machine-independent)"

p<-ggplot() + xlab('# implemented builtins') + ylab('percentage of\nsupported projects') +
    scale_linetype_manual(values=c("solid", "dotted", "F1", "dotdash"))+
    geom_line(data=greedy_libc, aes(x = nr_builtins, y = perc_projects, color=name, linetype=name)) +
    geom_line(data=greedy_nolibc, aes(x = nr_builtins, y = perc_projects, color=name, linetype=name)) +
    geom_line(data=most_frequent, aes(x = nr_builtins, y = perc_projects, color=name, linetype=name)) +
    geom_line(data=most_frequent_nolibc, aes(x = nr_builtins, y = perc_projects, color=name, linetype=name)) +
    scale_x_continuous(trans = log10_trans(), breaks=c(1, 10, 100, 1000, 3000)) +
    theme(panel.grid.major = element_blank(), 
        panel.grid.minor = element_blank(),
        panel.background = element_blank(),
        axis.line = element_line(colour = "black"),
        legend.key=element_blank(),
        legend.background = element_blank(),
        legend.title=element_blank(),
        legend.key.height=unit(1, "line"),
, axis.text = element_text(size = 5), axis.title = element_text(size = 7), strip.text = element_text(size = 7),         legend.text=element_text(size = 6),
legend.justification=c(-1.2,0.0), legend.position=c(0,0),
plot.margin = unit(c(0.1,0.1,0,0.1), "cm")
        )

ggsave(filename="../generated/plots/implementation.pdf", plot=p, width=8.45, height=4.5, units="cm")
