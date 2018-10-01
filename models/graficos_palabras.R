library(tidyverse)
library(ggthemes)
library(ggridges)
library(rjson)

grafico_listados <- function(listado){
  
  file = paste0("results/",listado,".csv") 
  results <- read_csv(file)  %>% 
    gather(revista,proporcion,1:(length(.)-2)) 
  
  sombreados <- results %>% 
    filter(signif == "False") %>% 
    mutate(x_min = year-0.5,
           x_max = year+0.5)
  
  g <- results %>% 
    ggplot(.,aes(year,proporcion, color = revista, group = revista))+
    geom_smooth(se = F,method = 'loess')+
    geom_point()+
    theme_tufte()+
    labs(x="Años", y="Tasa de aparición promedio", title = listado,
         caption = "en gris años no significativos")+
    scale_color_gdocs()+
    scale_x_continuous(breaks = c(2008:2018))
  
  
  if (nrow(sombreados)>0) {
    g <- g+geom_rect(data = sombreados, aes(xmin=x_min, xmax=x_max, ymin=-Inf, ymax=+Inf), fill='grey',color = NA, alpha=0.2)
  }
  
  return(g)
}


json_file = "palabras_a_trackear.json"
json_data <- fromJSON(paste(readLines(json_file), collapse=""))
listados <- names(json_data)


for (lista in listados) {
  grafico_listados(lista)
  ggsave(paste0("results/",lista,".png"),scale = 2)
}

