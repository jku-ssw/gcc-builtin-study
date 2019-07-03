# Plots Figure 5 (how well various tools perform on the GCC test cases)

library(ggplot2)
library(ggthemes)

data <- read.csv("../gcc-builtin-tests/tool-evaluation.csv")
data$Approach <- factor(data$Approach,levels = c("GCC 7.2 (2017)", "Clang 5.0 (2017)", "ICC 18.0.3 (2018)", "KLEE 1.4 (2017)", "Sulong c710bf2 (2017)", "DragonEgg 3.3 (2013)", "Frama-C Chlorine-20180501 (2018)", "Cilly 1.7.3 (2014)", "KCC 1.0 (2018)", "CompCert 3.3 (2018)", "TCC 0.9.27 (2017)"))
data$Error <- factor(data$Error, levels = c("Incorrect", "Missing", "Other error", "Correct"))
p <- ggplot(data, aes(x = Approach, y = Number, fill = Error)) +
                              geom_bar(stat = "identity") +
                              coord_flip() +
                              xlab("") +
                              ylab("Executed test cases") +
                              theme_bw() +
                              theme( legend.box.margin=margin(-10,-10,-10,-25), legend.position="bottom", plot.title = element_text(hjust = .5), legend.text = element_text(size=6),
                                    axis.ticks = element_blank(), legend.title=element_blank(), strip.background = element_blank(), panel.grid.major.x = element_blank(), axis.text = element_text(size = 5), axis.title = element_text(size = 7), strip.text = element_text(size = 7)) +
  scale_fill_manual(values=c("red", "orange", "royalblue", "chartreuse2"), guide = guide_legend(reverse = TRUE)) + guides(fill = guide_legend(keywidth = 0.65, keyheight = 0.65, override.aes=list(size = 0.2), reverse=TRUE))
ggsave(filename="../generated/plots/tool-evaluation.pdf", plot=p, width=8.45, height=5, units="cm")

