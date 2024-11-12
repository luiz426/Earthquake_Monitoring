 Sistema de Monitoramento de Terremotos em Tempo Real

Um sistema automatizado de coleta e análise de dados sísmicos utilizando Apache Airflow, Docker e PostgreSQL. O projeto coleta dados da API USGS (United States Geological Survey) e enriquece as informações com dados geográficos detalhados usando a API OpenCage.

Sobre o Projeto

Este sistema realiza o monitoramento contínuo de atividades sísmicas globais, coletando dados a cada 10 minutos e armazenando-os em um banco de dados PostgreSQL. O projeto utiliza Docker para containerização, garantindo consistência entre ambientes de desenvolvimento e produção.

Funcionalidades

Coleta automática de dados sísmicos da API USGS
Atualização a cada 10 minutos
Enriquecimento de dados com informações geográficas detalhadas (cidade, estado, país)
Rastreamento de alterações nos dados dos terremotos
Interface web para visualização dos dados (via pgAdmin)
Sistema de logging para monitoramento de estatísticas

Tecnologias Utilizadas

Python 3.x
Apache Airflow 2.10.2
PostgreSQL 16
Docker e Docker Compose
pgAdmin 4
Redis 7.2
OpenCage Geocoding API
USGS Earthquake API

 Estrutura do Projeto

Copyearthquake-monitoring/
dags/
earthquake_monitoring.py    
docker-compose.yml             
logs/                         
plugins/                      
README.md

Requisitos

Docker e Docker Compose instalados
Chave de API do OpenCage (gratuita)
Mínimo de 4GB de RAM
Mínimo de 2 CPUs
Mínimo de 10GB de espaço em disco

Estrutura do Banco de Dados

Tabela: earthquakes

id: Identificador único do terremoto
time: Data e hora do evento
latitude/longitude: Coordenadas
depth: Profundidade
magnitude: Magnitude do terremoto
place: Localização descritiva
type: Tipo do evento
alert: Nível de alerta
tsunami: Indicador de risco de tsunami
Dados geográficos enriquecidos (cidade, estado, país)

Tabela: earthquake_updates

Rastreamento de alterações nos dados
Histórico de atualizações por evento

Pipeline de Dados

Coleta: Dados obtidos da API USGS a cada 10 minutos
Enriquecimento: Dados geográficos adicionados via OpenCage API
Processamento: Verificação de atualizações e novos eventos
Armazenamento: Persistência no PostgreSQL
Monitoramento: Estatísticas e logs de eventos

Monitoramento

O sistema gera estatísticas automáticas incluindo:

Contagem de eventos por país
Magnitudes médias por região
Atualizações de dados existentes
Performance da pipeline

Observações Importantes

A API do OpenCage tem limite de requisições
Implementado delay de 2 segundos entre chamadas à API
Sistema de fallback para coordenadas quando geocodificação falha
Índices otimizados para consultas frequentes
