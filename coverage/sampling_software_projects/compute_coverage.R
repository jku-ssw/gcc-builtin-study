# SAMPLING SOFTWARE PROJECTS
# Microsoft Research License Agreement
# Non-Commercial Use Only 
# For the full license, please see file License.txt
#
# (c) Microsoft Corporation. All rights reserved. 


## Similarity functions

create.numeric.similarity.sd <- function(value.project, values.universe) {
  stddev <- sd(values.universe)
  function(value.other.project) { 
    value.project - stddev <= value.other.project & value.other.project <= value.project + stddev 
  }
}

create.numeric.similarity <- function(value.project, values.universe) {
  lower <- 10 ^ (log10(value.project+1) - 0.5) - 1 
  upper <- 10 ^ (log10(value.project+1) + 0.5) - 1
  function(value.other.project) { 
    lower <= value.other.project & value.other.project <= upper 
  }
}

create.factor.similarity <- function(value.project, values.universe) {
  function(value.other.project) { 
    value.project == value.other.project 
  }
}


## score a sample of projects in a universe for a given space

score.projects <- function(sample, universe, space, configuration=NA) {
  variables <- all.vars(space)

  if ( length(setdiff(variables, names(sample))) > 0 ) 
    stop(gettextf("variables '%s' not found in sample", paste(setdiff(variables, names(sample)), collapse=", ")), domain = NA)             

  if ( length(setdiff(variables, names(universe))) > 0 ) 
    stop(gettextf("variables '%s' not found in universe", paste(setdiff(variables, names(universe)), collapse=", ")), domain = NA)             

  project_var <- variables[1]
  dimension_vars <- variables[-1]
  
  dim_index_matrix <- matrix(rep(F, length=length(dimension_vars)*nrow(universe)), 
                             nrow=length(dimension_vars), ncol=nrow(universe), byrow=T)
  index_set <- rep(F, length=nrow(universe))
  
  if (nrow(sample)>0) for (pid in 1:nrow(sample)) {
    project_index_set <- rep(T, length=nrow(universe))

    for (dim in 1:length(dimension_vars)) {
      dimension <- dimension_vars[dim]
      
      if (dim <= length(configuration) & !is.na(configuration[dim])) {
        is.similar <- configuration[[dim]](sample[pid,dimension], universe[,dimension])
        d <- is.similar(universe[,dimension])      
      }
      else if (is.numeric(universe[,dimension])) {
        is.similar <- create.numeric.similarity(sample[pid,dimension], universe[,dimension])
        d <- is.similar(universe[,dimension])
      }
      else if (is.factor(universe[,dimension])) {
        is.similar <- create.factor.similarity(sample[pid,dimension], universe[,dimension])
        d <- is.similar(universe[,dimension])
      }
      else {
        stop(gettextf("no similarity function defined for '%s'", dimension, domain = NA))         
      }
      
      dim_index_matrix[dim,] <- dim_index_matrix[dim,] | d
      project_index_set <- project_index_set & d
    }
    index_set <- index_set | project_index_set
  }
  
  score <- sum(index_set, na.rm=T)/length(index_set)
  dimension_score <- apply(dim_index_matrix, 1, function(x) { sum(x, na.rm=T)/length(x) })
  return(list(dimensions=dimension_vars,
              score=score, dimension.score=dimension_score,
              score.indexset=index_set, dimension.indexset=dim_index_matrix))
}


## Compute the N next projects that if added to the sample maximize the score

next.projects <- function(N, sample, universe, space, configuration=NA) {

  start_time <- Sys.time()
  variables <- all.vars(space)
  
  if ( length(setdiff(variables, names(sample))) > 0 ) 
    stop(gettextf("variables '%s' not found in sample", paste(setdiff(variables, names(sample)), collapse=", ")), domain = NA)             
  
  if ( length(setdiff(variables, names(universe))) > 0 ) 
    stop(gettextf("variables '%s' not found in universe", paste(setdiff(variables, names(universe)), collapse=", ")), domain = NA)             
  
  dimension_vars <- variables[-1]

  candidates <- universe
  candidates$score.increase <- 1

  result <- sample[-1:-nrow(sample),]

  print(paste("Computing similarity matrix... This may take a while, please be patient.", Sys.time()))
  
  similar_project_matrix <- matrix(data=F, nrow=nrow(candidates), ncol=nrow(universe), byrow=T)

  for (pid in 1:nrow(candidates)) {
      
    project_index_set <- rep(T, length=nrow(universe))

    for (dim in 1:length(dimension_vars)) {
      dimension <- dimension_vars[dim]
        
      if (dim <= length(configuration) & !is.na(configuration[dim])) {
        is.similar <- configuration[[dim]](candidates[pid,dimension], universe[,dimension])
        d <- is.similar(universe[,dimension])      
      }
      else if (is.numeric(candidates[,dimension])) {
        is.similar <- create.numeric.similarity(candidates[pid,dimension], universe[,dimension])
        d <- is.similar(universe[,dimension])
      }
      else if (is.factor(candidates[,dimension])) {
        is.similar <- create.factor.similarity(candidates[pid,dimension], universe[,dimension])
        d <- is.similar(universe[,dimension])
      }
      else {
        stop(gettextf("no similarity function defined for '%s'", dimension, domain = NA))         
      }
      project_index_set <- project_index_set & d
    }
    similar_project_matrix[pid,] <- project_index_set
  }
  
  print(paste("Computing similarity matrix... Done", Sys.time()))

  # Initial score
  sc <- score.projects(rbind(sample, result[,1:ncol(sample)]), universe, space, configuration)
  sc.score <- sc$score
  sc.score.indexset <- sc$score.indexset
  
  print(paste("Finding next projects... This may take a while, please be patient.", Sys.time()))
  
  # Compute n next projects
  num_projects = nrow(universe)
  candidate_list <- 1:nrow(candidates)
  for (n in 1:N) {    
    best.increase.sofar <- 0
    
    count <- 0
    for (pid in candidate_list) {
      if (best.increase.sofar >= candidates[pid,]$score.increase) break;
      count <- count + 1
      index_set <- sc.score.indexset | similar_project_matrix[pid,]
      score <- sum(index_set, na.rm=T)/num_projects
      
      candidates[pid,]$score.increase <- score - sc.score
      best.increase.sofar <- max(candidates[pid,]$score.increase, best.increase.sofar)
    }

    new_order = order(candidates$score.increase, decreasing=T, na.last=NA)
    best.increase.row <- new_order[1]
    result = rbind(result, candidates[best.increase.row,])
    sc.score.indexset <- sc.score.indexset | similar_project_matrix[best.increase.row,]
    sc.score <- sum(sc.score.indexset, na.rm=T)/num_projects
    candidates[best.increase.row,]$score.increase <- NA
    
    candidate_list = new_order[-1]
    
    print(paste("Found", n, "projects. New score", sc.score, Sys.time()))
    
    if (sc.score>=1.0) break; # we have covered everything
  }

  sc <- score.projects(rbind(sample, result[,1:ncol(sample)]), universe, space, configuration)
  return(list(new.projects=result, score=sc))
}

# url <- "http://sailhome.cs.queensu.ca/replication/representativeness/masterdata.txt"
# ohloh <- read.delim(url, header=T, na.strings=c("", "NA"))
# sample <- ohloh[ohloh$name=="Mozilla Firefox",]
# score <- score.projects(sample, universe=ohloh, id ~ total_code_lines + twelve_month_contributor_count)

# np <- next.projects(10, sample, universe=ohloh, id ~ total_code_lines + twelve_month_contributor_count)

# score.2 <- score.projects(sample, universe=ohloh, id ~ total_code_lines + twelve_month_contributor_count, configuration=c(create.numeric.similarity.sd, NA))

universe <- read.csv("../cprojects.csv")
builtin_projects <- read.csv("../builtinprojects.csv")
score <- score.projects(builtin_projects, universe=universe, repository~ architecture + community + continuous_integration + documentation + history + issues + license + size + unit_test + scorebased_org)
print(score$score)
print(score$dimension.score)
