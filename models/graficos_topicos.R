library(tidyverse)
library(ggthemes)
library(ggridges)
results <- read_csv("results/topicos_results.csv")


results %>% 
  gather(Topico,proporcion,3:length(.)) %>%
  mutate(year = factor(year, levels = unique(results$year))) %>% 
  ggplot(.,aes(year,proporcion, color = revista, group = revista))+
  geom_smooth(se = F,method = 'loess')+
  geom_point()+
  theme_tufte()+
  labs(x="Años", y="Tasa de aparición promedio por tópico", title = "Evolución de los tópicos")+
  scale_color_gdocs()+
  facet_wrap(~Topico, scales = "free")

ggsave("results/evol_topicos_agregado.png",scale = 2)


#### Con todos los datos


results <- read_csv("results/topicos_results_all.csv")
#para que el gráfico quede proporcional, necesito que haya la misma cantidad de observaciones de cada revista

results <- results %>% 
  select(-X1,`Objetivacion Mujer`= `objetivacion mujer`) %>% 
  gather(Topico,proporcion,3:length(.)) %>%
  mutate(year = factor(year, levels = unique(results$year)))

balanceo <- function(results){
  n <- results %>% 
    group_by(revista,year) %>% 
    summarise(n = n()) %>% 
    group_by(year) %>% 
    summarise(n = min(n))
  balanced = data_frame()
  for (nano in unique(results$year)) {
    tmp <- results %>% 
      filter(year == nano) %>% 
      group_by(revista) %>% 
      sample_n(size = n$n[n$year==nano])
    balanced <- bind_rows(balanced,tmp)
  }
  return(balanced)
}

balanced_df <- balanceo(results)


ggplot(balanced_df,aes(year,proporcion, color = revista, group = revista))+
  geom_jitter(alpha=0.5,height = 0,width = .5)+
  geom_rug(sides = "l")+
  theme_tufte()+
  labs(x="Años", y="Proporción por tópico por artículo", title = "Evolución de los tópicos",
       caption = "para cada año, se muestra una misma cantidad de artículos por revista")+
  scale_color_gdocs()+
  facet_wrap(~Topico, scales = "free")

ggsave("results/evol_topicos_articulos.png",scale = 2)


ggplot(balanced_df,aes(year,proporcion, color = revista, group = revista))+
  geom_smooth()+
  theme_tufte()+
  labs(x="Años", y="Proporción por tópico por artículo", title = "Evolución de los tópicos",
       caption = "para cada año, se muestra una misma cantidad de artículos por revista")+
  scale_color_gdocs()+
  facet_wrap(~Topico, scales = "free")
ggsave("results/evol_topicos_smooth.png",scale = 2)


### Densidades
results %>% 
  filter(proporcion>5e-04) %>% 
ggplot(.,aes(x =proporcion,y=Topico, fill = revista))+
  geom_density_ridges(alpha = 0.75) +
  scale_fill_gdocs()+
  scale_x_continuous(limits = c(0,0.1),expand = c(0,0)) +
  theme_tufte()

  

#### Test de significatividad
#Test de Mann Whitney. Es el que mejor se ajusta al problema. Testea, de dos muestras independientes, que provienen 
#de una misma distribución, si una esta corrida respecto de la otra. 
for (ano in c(2008:2018)) {
  print("-------------")
  print(ano)
  a <- results %>%
    filter(year== ano,Topico=="Objetivacion Mujer") %>%
    wilcox.test(proporcion ~ revista, data=.)
  print(a)

}

p_vaules <- results %>% 
  group_by(year,Topico) %>% 
  summarise(p_test_wilcox = wilcox.test(proporcion~revista, data= .)$p_vaules)
#dan todos 0!

#Test de Kolmogorov Smirnov. Testea si dos muestras provienen de una misma distribución. 
#En realidad, dado nuestro modelo de LDA, ambas revistas vienen de un mismo proceso generador de datos.
for (ano in c(2008:2018)) {
  print("-------------")
  print(ano)
  filtro <- results %>%
    filter(year== ano,Topico=="Objetivacion Mujer")
  
  a <- ks.test(filtro$proporcion[filtro$revista=="ohlala"],
                   filtro$proporcion[filtro$revista=="brando"])
  print(a)
  
}

## dan todos raro!
