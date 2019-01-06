#Cargo las librerias
paquetes <- c("tidyverse", "lubridate", "igraph")

for (i in seq_along(paquetes)) {
  if (!require(paquetes[[i]], character.only = TRUE)) 
  {install.packages(paquetes[[i]])}
  require(paquetes[[i]], character.only = TRUE)
}

#Defino el theme con el que trabajar
theme_set(theme_minimal())

#Cargo las bases
firmantes <- read_csv("data_estatica/proyectos_congreso_firmantes.csv")
dip_giros <- read_csv("data_estatica/proyectos_congreso_giros_diputados.csv")
sen_giros <- read_csv("data_estatica/proyectos_congreso_giros_senado.csv")
expedientes <- read_csv("data_estatica/proyectos_congreso_expedientes.csv")
tramites <- read_csv("data_estatica/proyectos_congreso_tramites.csv")

## ANALISIS EXPEDIENTES ####
expedientes <- 
  expedientes %>% 
  rename(iniciado_en = `Iniciado en`, 
         publicado_en = `Publicado en`,
         exp_diputados = `Expediente Diputados`,
         exp_senado = `Expediente Senado`,
         fecha = Fecha)

#Por publicacion
expedientes %>% 
  group_by(publicado_en) %>% 
  summarise(n = n()) %>% 
  arrange(desc(n)) %>% 
  filter(!is.na(publicado_en)) %>% 
  top_n(10, n)

#Por fecha
expedientes %>% 
  mutate(fecha = as.Date(fecha, format = "%d/%m/%Y")) %>% 
  ggplot() +
  geom_histogram(aes(fecha), bins = 240) +
  scale_x_date(date_breaks = 'year', date_labels = '%Y') +
  labs(title = "Cantidad de proyectos según fecha", x = "Año", y = "")

## ANALISIS FIRMANTES ####
#Por bloque y persona
firmantes %>% 
  filter(!str_detect(firmante, "MIXTA REVISORA DE CUENTAS")) %>% 
  group_by(firmante, bloque) %>% 
  summarise(n = n()) %>% 
  ungroup() %>% 
  arrange(desc(n)) %>%
  top_n(10, n) %>% 
  ggplot() +
  geom_col(aes(reorder(firmante, n), n, fill = bloque, group = bloque)) +
  coord_flip() +
  labs(title = "Cantidad de proyectos por firmante", x = "", y = "")

#Por bloque
firmantes %>% 
  filter(!is.na(bloque)) %>% 
  group_by(bloque) %>% 
  summarise(n = n()) %>% 
  ungroup() %>% 
  arrange(desc(n)) %>%
  top_n(10, n) %>% 
  ggplot() +
  geom_col(aes(reorder(bloque, n), n)) +
  coord_flip() +
  labs(title = "Cantidad de proyectos por bloque", x = "", y = "")

## ANALISIS TRAMITES ###
#Por tipo y camara
tramites %>% 
  group_by(tipo, camara) %>% 
  summarise(n = n()) %>%
  ungroup() %>% 
  arrange(desc(n)) %>% 
  top_n(7, n) %>% 
  ggplot() +
  geom_col(aes(reorder(tipo, n), n, fill = camara, group = camara), position = "dodge") +
  coord_flip() +
  labs(title = "Cantidad de proyectos por tipo y Cámara")
  
#Por tipo y movimiento
tramites %>% 
  group_by(tipo, movimiento) %>% 
  summarise(n = n()) %>%
  ungroup() %>% 
  arrange(desc(n)) %>% 
  top_n(10, n) %>% 
  ggplot() +
  geom_col(aes(reorder(tipo, n), n, fill = movimiento, group = movimiento), position = "dodge") +
  coord_flip() +
  labs(title = "Cantidad de proyectos por tipo y Cámara") +
  theme(legend.position = "bottom")

## ANALISIS GIROS ####
#Por giros Diputados
dip_giros %>% 
  group_by(giro_a_comision) %>% 
  summarise(n = n()) %>% 
  arrange(desc(n))

#Por giros Senado
sen_giros %>% 
  group_by(giro_a_comision) %>% 
  summarise(n = n()) %>% 
  arrange(desc(n))

#Giros por bloque (Diputados)
dip_giros %>% 
  left_join(firmantes, by = "expediente") %>% 
  group_by(bloque, giro_a_comision) %>% 
  summarise(n = n()) %>% 
  ungroup() %>% 
  arrange(desc(n)) %>% 
  top_n(20, n) %>% 
  ggplot() +
  geom_col(aes(reorder(giro_a_comision, n), n, group = bloque, fill = bloque), 
           position = "dodge", width = 0.5) +
  coord_flip() +
  theme(legend.position = "bottom") +
  labs(title = "Proyectos según giro", x = "Comisión", y = "")

#Giros por bloque (Senado)
sen_giros %>% 
  filter(!str_detect(giro_a_comision, "PARLAMENTARIA MIXTA REVISORA")) %>% 
  left_join(firmantes, by = "expediente") %>% 
  group_by(bloque, giro_a_comision) %>% 
  summarise(n = n()) %>% 
  ungroup() %>% 
  arrange(desc(n)) %>% 
  top_n(30, n) %>% 
  ggplot() +
  geom_col(aes(reorder(giro_a_comision, n), n, group = bloque, fill = bloque), 
           position = "dodge", width = 0.5) +
  coord_flip() +
  theme(legend.position = "bottom") +
  labs(title = "Proyectos según giro", x = "Comisión", y = "")

## INTENTO ARMAR UN GANTT DE LAS COMISIONES ####
# Custom theme for making a clean Gantt chart
theme_gantt <- function(base_size=11) {
  ret <- theme_bw(base_size) %+replace%
    theme(panel.background = element_rect(fill="#ffffff", colour=NA),
          axis.title.x=element_text(vjust=-0.2), axis.title.y=element_text(vjust=1.5),
          panel.border = element_blank(), axis.line=element_blank(),
          panel.grid.minor=element_blank(),
          panel.grid.major.y = element_blank(),
          panel.grid.major.x = element_line(size=0.5, colour="grey80"),
          axis.ticks=element_blank(),
          legend.position="bottom", 
          axis.title=element_text(size=rel(0.8)),
          strip.text=element_text(size=rel(1)),
          strip.background=element_rect(fill="#ffffff", colour=NA),
          panel.spacing.y=unit(1.5, "lines"),
          legend.key = element_blank())
  
  ret
}

#Gantt de creación de comisiones en Diputados
dip_giros %>% 
  group_by(giro_a_comision) %>% 
  mutate(year = str_extract(expediente, "[\\d]+$"),
         min_date = min(year),
         max_date = max(year)) %>% 
  filter(!is.na(year), min_date> 1999) %>% 
  distinct(giro_a_comision, min_date, max_date) %>% 
  gather(date_type, task_date, -giro_a_comision) %>% 
  ungroup() %>% 
  ggplot(aes(x=giro_a_comision, y=as.Date(task_date, format = '%Y'))) + 
  geom_line() + 
  guides(colour=guide_legend(title=NULL)) +
  labs(x="", y="", title = "Duración de las comisiones en Diputados", 
       subtitle = "Creadas después de 1999") + 
  coord_flip() +
  scale_y_date(date_breaks="1 year", date_labels = "%Y") +
  theme_gantt()
  
#Gantt de creación de comisiones en Senado
sen_giros %>% 
  group_by(giro_a_comision) %>% 
  mutate(year = str_extract(expediente, "[\\d]+$"),
         min_date = min(year),
         max_date = max(year)) %>% 
  filter(!is.na(year), min_date> 1999) %>% 
  distinct(giro_a_comision, min_date, max_date) %>% 
  gather(date_type, task_date, -giro_a_comision) %>% 
  ungroup() %>% 
  ggplot(aes(x=giro_a_comision, y=as.Date(task_date, format = '%Y'))) + 
  geom_line() + 
  guides(colour=guide_legend(title=NULL)) +
  labs(x="", y="", title = "Duración de las comisiones en Senado", 
       subtitle = "Creadas después de 1999") + 
  coord_flip() +
  scale_y_date(date_breaks="1 year", date_labels = "%Y") +
  theme_gantt()

#Proyectos por Cámara y cantidad de personas
firmantes %>% 
  left_join(expedientes, by = c("expediente", "tipo", "titulo")) %>% 
  filter(!(firmante %in% c("H CAMARA DE DIPUTADOS", "PARLAMENTARIA MIXTA REVISORA DE CUENTAS"))) %>%
  filter(!(iniciado_en %in% c("1", "cDiputados"))) %>% 
  group_by(expediente, iniciado_en) %>% 
  summarise(n = n()) %>% 
  ggplot(aes(n, colour = iniciado_en)) +
  stat_ecdf() +
  scale_x_log10() +
  scale_y_log10() +
  labs(title = "Proyectos según cantidad de firmantes y Cámara de origen",
       x = "Firmantes", y = "% proyectos", colour = "Cámara \n de origen")

grafo_firmantes <- firmantes %>% 
  mutate(firmante2 = firmante) %>% 
  select(expediente, firmante, firmante2) %>% 
  group_by(expediente) %>% 
  filter(n() > 1) %>% 
  expand(firmante, firmante2) %>% 
  filter(firmante != firmante2) %>% 
  select(-expediente)
