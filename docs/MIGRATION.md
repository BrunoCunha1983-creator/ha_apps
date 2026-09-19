# Plano de migração para ha_apps

Este ficheiro é o inventário principal dos projetos relacionados com Home Assistant.

## Estrutura alvo

- `integrations/` — custom integrations / `custom_components`
- `cards/` — Lovelace/frontend
- `esphome/` — ESPHome e presença
- `addons/` — add-ons HA OS/Supervisor
- `services/` — serviços auxiliares usados pelo HA (Traccar, geocoder, bridges, etc.)
- `automations/` — automações reutilizáveis
- `blueprints/` — blueprints
- `packages/` — packages
- `dashboards/` — Lovelace/dashboards
- `installations/` — configurações completas Casa/Caravana
- `external/` — forks/dependências externas que não queremos absorver diretamente

# A. Integrações já existentes no GitHub

## Confirmadas como custom integrations

### ha-residuosPT
- Repositório antigo: `ha-residuosPT`
- Domain atual: `recolha_residuos_pt`
- Destino: `integrations/recolha_residuos_pt/`

### astro_tracker
- Repositório antigo: `astro_tracker`
- Domain atual: `astro_tracker`
- Inclui também conteúdo Lovelace.
- Destino principal: `integrations/astro_tracker/`
- Lovelace reutilizável: `dashboards/astro_tracker/`

### ha-offcloud
- Repositório antigo: `ha-offcloud`
- Domain atual: `offcloud`
- Destino: `integrations/offcloud/`

### ha-plugins
Repositório misto. Não deve ser copiado inteiro para uma única pasta.

Conteúdo confirmado:
- `custom_components/pingo_doce_plus` → `integrations/pingo_doce_plus/`
- `ha-sip/` e componentes SIP → avaliar para `addons/` ou `services/`
- `pingo-doce/` / `pingo_doce_plus/` → manter apenas a implementação ativa/canónica

### ha-eredes
- Destino: `integrations/eredes_pt/`

### ha-sql_json
- Destino: `integrations/sql_json/`

### ha-uber-eats
- Destino: `integrations/uber_eats/`

### ha-custom-component-coverflex
- Destino: `integrations/coverflex/`

### hass-geolocator
- Destino: `integrations/geolocator/`

### ha-life360
- Verificar se é fork/upstream antes de absorver.
- Se for versão mantida por nós: `integrations/life360/`

### WeatherXM-Home-Assistant
- Verificar origem/fork.
- Destino se mantido por nós: `integrations/weatherxm/`

### home-assistant-custom-components-door-window-advisor
- Destino se mantido por nós: `integrations/door_window_advisor/`

### homeassistant-plant
- Verificar upstream.
- Destino se mantido por nós: `integrations/plant/`

### ha-mcp
- Projeto HA/MCP.
- Destino previsto: `integrations/ha_mcp/` e/ou `services/mcp/`, conforme separação do código.

# B. Integrações/projetos HA recuperados das nossas conversas

## Localização, GPS e GSM

### gpsd_advanced
Projeto **GPSD Advanced**.
- GPSD TCP
- `device_tracker`
- latitude/longitude
- altitude
- velocidade
- rumo
- satélites
- HDOP/PDOP/VDOP
- sensores de viagem/direção
- mapa no HA
- GPS USB/u-blox
- suporte a GPSD remoto

Destino: `integrations/gpsd_advanced/`

Nomes/experiências anteriores a consolidar aqui:
- `gpsd_tracker`
- `USBGPS`
- GPSD Source Manager
- GPSD Advanced
- GPSD Weather Tracker (parte GPS)

### gsm_tracker
Projeto **GSM Tracker** para autocaravana/veículos.
- ESP32 + GSM/GPRS/LTE
- GPS
- MQTT/HA
- `device_tracker`
- telemetria
- possibilidade de OBD2
- localização por rede/célula como fallback

Destino:
- integração HA: `integrations/gsm_tracker/`
- firmware ESPHome/ESP32: `esphome/gsm_tracker/`

### cellular_router
Integração universal para routers/modems 4G/5G.
- estado SIM
- operadora
- sinal
- tecnologia celular
- GPS quando disponível
- dados de rede
- possibilidade SNMP/HTTP/serial/USB

Destino: `integrations/cellular_router/`

### gpsd_weather_tracker
Projeto combinado GPS + meteorologia.
- posição via GPSD
- reverse geocoding
- weather por posição
- `device_tracker`

A funcionalidade comum de GPS deve reutilizar `gpsd_advanced`.

Destino previsto: `integrations/gpsd_weather_tracker/`

## Transportes e localização

### metro_lisboa
- estado das linhas
- estações
- tempos/dados em tempo real
- autenticação/API oficial
- sensores e `device_tracker` de estações

Destino: `integrations/metro_lisboa/`

### carris
Projeto de dados Carris/Carris Metropolitana.
Destino: `integrations/carris/`

### traccar-geocoder
O repositório atual é um serviço Docker/Rust de reverse geocoding, não um `custom_component`.

Destino correto: `services/traccar_geocoder/`

Pode ser consumido por:
- GPSD Advanced
- GSM Tracker
- Traccar
- autocaravana
- outros `device_tracker`

## Serviços públicos / Portugal

### simar
- avisos/roturas
- freguesias
- sensores/binary sensors
- mapa
- config flow

Destino: `integrations/simar/`

### fogos_pt
- Fogos.pt
- incêndios
- zonas/raio
- alertas
- trackers/mapa

Destino: `integrations/fogos_pt/`

### ocorrencias_ativas_pt
- incêndios
- acidentes
- inundações
- deslizamentos
- sensores globais/por zona
- trackers no mapa
- notificações

Destino: `integrations/ocorrencias_ativas_pt/`

### eredes_pt
Projeto E-Redes / energia.
Destino: `integrations/eredes_pt/`

### recolha_residuos_pt
Já existe em `ha-residuosPT`.
Destino: `integrations/recolha_residuos_pt/`

## Casa / serviços / consumo

### offcloud
Já existe em `ha-offcloud`.
Destino: `integrations/offcloud/`

### pingo_doce_plus
Já existe dentro de `ha-plugins`.
Destino: `integrations/pingo_doce_plus/`

### candy_simplyfi
Existe também o repositório `CandySimplyFi-tool`.
Objetivo: integração/local control Candy Simply-Fi.
Destino previsto: `integrations/candy_simplyfi/` e ferramentas auxiliares em `services/candy_simplyfi/`.

### nosnet
Projeto para Internet/router NOS e respetivas entidades.
Destino previsto: `integrations/nosnet/`.

### mold_risk
Projeto/sensores de risco de bolor.
Destino previsto: `integrations/mold_risk/` ou `packages/mold_risk/`, consoante a implementação final.

## PBX / telefonia dentro do Home Assistant

### freepbx_bridge
- Asterisk/FreePBX
- AMI/ARI
- chamadas/eventos
- estado de extensões

Destino: `integrations/freepbx_bridge/`

### ht503
Integração HA para Grandstream HT503.
- FXS/FXO
- SIP
- firmware
- uptime
- estado
- ações de refresh/reboot

Destino: `integrations/ht503/`

### ha-sip
Parte do atual `ha-plugins`.
Como inclui gateway/serviço, deve ser separado entre:
- `integrations/ha_sip/` quando houver componente HA
- `services/ha_sip/` para backend/gateway
- `addons/ha_sip/` se existir pacote Supervisor

O projeto independente `gsm2sip-gateway` continua fora do `ha_apps` como produto Asterisk/GSM/SIP, embora possa ter uma integração HA cliente neste monorepo.

## Voz / bots / media

Projetos atuais relacionados:
- `voice-satellite-card-integration`
- `Voice-Satellite-Card-for-Home-Assistant`
- `HAMusicAssistantJukebox`
- `rgnlabs-mediaplayer`
- `spotify-voice-assistant`
- `linux-voice-assistant`
- `dash-voice`
- `hass_discord_bot`
- `homeassistant-discord-bot`

Separar entre:
- `integrations/`
- `cards/`
- `services/`
conforme cada componente.

# C. ESPHome

Projetos atuais/planeados:
- `esphome-ugreen-hdmi-switcher`
- `esphome-presence`
- ESPresense compatível com ESPHome
- BLE presence
- GSM Tracker firmware
- sensores adicionais DHT22/lux/etc.

Destino: `esphome/<projeto>/`

# D. Lovelace / frontend

Candidatos atuais:
- `dual-gauge-card`
- `Voice-Satellite-Card-for-Home-Assistant`
- `au-fire-risk-card`
- `status-card`
- `HA-Animated-cards`
- `Home-Assistant-Lovelace-HTML-Jinja2-Template-card`
- `o365-card`
- `lovelace-hui-element`
- `lovelace-state-switch`
- `circle-sensor-card`
- `button-card`
- `lovelace-more-info-card`
- `alarm-clock-card`
- `home-assistant-cards`

Destino: `cards/<nome>/`

Antes de absorver forks, confirmar se queremos realmente manter uma versão própria.

# E. Instalações completas

- `HassIO-Casa` → `installations/casa/`
- `HassIO-Caravana` → `installations/caravana/`

Antes de migrar:
- remover secrets
- tokens
- passwords
- API keys
- identificadores privados

# F. Forks/dependências externas

Não absorver automaticamente forks só para esconder repositórios.

Exemplos:
- `hass-roborock`
- `room-assistant`
- `HASS.Agent`
- `HASS.Agent-MediaPlayer`
- `HASS.Agent-Notifier`
- `alerts.home-assistant.io`
- `Home-Assistant-Mail-And-Packages`

Manter referência em `external/` e só criar uma versão interna quando houver alterações nossas que justifiquem manutenção própria.

# G. Regra de migração

Para cada repositório:
1. identificar se é nosso, fork ou dependência;
2. identificar o tipo real;
3. verificar secrets/credenciais;
4. importar para a pasta correta;
5. adaptar imports/workflows/HACS;
6. testar;
7. só então marcar o repositório antigo como legado/arquivo.

Nunca apagar o repositório antigo antes da validação.

# H. Projetos que ficam fora de ha_apps

- **FiveM / Zombie** → projetos FiveM.
- **Proxmox / servidores / IA** → Prox-AI, mcp-proxmox, ProxmoxVE, etc.
- **Asterisk / GSM / SIP standalone** → gsm2sip-gateway, Asterisk, chan_dongle, AVA, etc.
- **Farming Simulator 25** → mods e ferramentas FS25.
- **Windows / rede / utilitários** → ferramentas Windows, VPN, DDNS, scripts de rede.
