# Plots Figure 1 (number of architecture-specific and architecture-independent builtins per project)

library(ggplot2)
library(reshape)
library(scales)

df1<-read.csv(file="../generated/unique_builtins_per_category.csv",header=TRUE,sep=";")
df1$occurrences <- "unique\noccurrences"
df2<-read.csv(file="../generated/builtins_per_category.csv",header=TRUE,sep=";")
df2$occurrences <- "non-unique\noccurrences"
df<-rbind(df1,df2)
p<-ggplot(df, aes(x=category, y=count)) + geom_boxplot() + scale_y_continuous(trans = 'log10',
                        breaks = trans_breaks('log10', function(x) 10^x),
                        labels = waiver()) + theme_bw() + theme(strip.background = element_blank(), axis.title.x = element_blank(), axis.text = element_text(size = 5), axis.title = element_text(size = 6), strip.text = element_text(size = 6)) + facet_grid(occurrences~., scales="fixed") +
                        coord_flip()
ggsave(filename="../generated/plots/boxplot_unique_cat.pdf", plot=p, width=8.45, height=5, units="cm")
