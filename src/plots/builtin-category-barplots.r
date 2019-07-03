# Plots Figure 2 (number of projects that rely on architecture-independent and architecture-specific builtins)

library(ggplot2)
library(reshape)

df1<-read.csv(file="../generated/platform-specific-builtins-in-projects.csv",header=TRUE,sep=";")
df1$type <- "architecture-specific"
df2<-read.csv(file="../generated/platform-independent-builtins-in-projects.csv",header=TRUE,sep=";") 
df2$type <- "architecture-independent"
df2 <- rbind(df1, df2)
df2$category <- factor(df2$category, levels = df2$category[order(df2$projects, decreasing = TRUE)])
print(df2)
g <- ggplot(data=df2, aes(x=category, y=projects)) + theme_bw()+
  theme(axis.text.x = element_text(angle=40, hjust=1, size=6), axis.title.x = element_blank(), strip.background = element_blank(), panel.grid.major.x = element_blank(), axis.text = element_text(size = 5), axis.title = element_text(size = 7), strip.text = element_text(size = 7), plot.margin = unit(c(-0.1,0.1,0,0.1), "cm")) + ylab("# projects") +
  geom_bar(stat="identity",position="dodge", fill="white", col="black") + facet_wrap(~type, nrow=1, scales="free_x")
ggsave(filename="../generated/plots/platform-dependent-and-independent-in-projects.pdf", plot=g, width=16.9, height=4, units="cm")
