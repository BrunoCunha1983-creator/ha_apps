# Plano de migração para ha_apps

Este ficheiro serve para consolidar os projetos de Home Assistant sem perder o histórico nem misturar forks externos com código mantido por nós.

## 1. Projetos próprios / candidatos a consolidar

### Custom integrations
- `ha-eredes`
- `hass-geolocator`
- `ha-sql_json`
- `ha-uber-eats`
- `ha-custom-component-coverflex`
- `home-assistant-custom-components-door-window-advisor`
- `homeassistant-plant`
- `ha-mcp`
- `voice-satellite-card-integration`
- `WeatherXM-Home-Assistant`
- `Home-Assistant-custom-components-Antistorm`
- `hassio-whoop`
- `ha-residuosPT`

Destino: `integrations/<domain>/`.

### Lovelace / frontend
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

Destino: `cards/<nome>/`.

### ESPHome / hardware
- `esphome-ugreen-hdmi-switcher`

Destino: `esphome/<nome>/`.

### Voz / media / satélites
- `HAMusicAssistantJukebox`
- `rgnlabs-mediaplayer`
- `spotify-voice-assistant`
- `linux-voice-assistant`
- `dash-voice`

Destino conforme o conteúdo: `integrations/`, `cards/` ou `scripts/`.

### Configurações completas de instalações HA
- `HassIO-Casa`
- `HassIO-Caravana`

Estas não devem ser misturadas com custom integrations. Destino recomendado:
- `installations/casa/`
- `installations/caravana/`

Antes de importar, remover segredos, tokens, passwords, chaves API e dados privados.

## 2. Forks / dependências externas

Projetos externos que apenas queremos acompanhar devem continuar como forks independentes enquanto precisarmos de sincronização com o upstream. No `ha_apps`, manter apenas um índice em `external/`.

Exemplos que precisam de verificação antes de serem importados:
- `hass-roborock`
- `room-assistant`
- `HASS.Agent`
- `HASS.Agent-MediaPlayer`
- `HASS.Agent-Notifier`
- `alerts.home-assistant.io`
- `Home-Assistant-Mail-And-Packages`

## 3. Regra de migração

Para cada repositório:
1. confirmar se é projeto nosso ou fork;
2. identificar o tipo de projeto;
3. verificar segredos e ficheiros grandes;
4. importar para a subpasta correta;
5. testar Home Assistant / HACS quando aplicável;
6. só depois marcar o repositório antigo como legado/arquivo.

Nunca apagar o repositório antigo antes de confirmar que o código consolidado funciona.

## 4. Outros grupos do GitHub

Os projetos que não são Home Assistant devem ficar separados por área:

- **FiveM / Zombie:** `fivem-autonomous-developer`, `The-Apocalypse-Project`, `Total-Apocalypse`, scripts QBCore/ESX e bots FiveM.
- **Proxmox / servidores / IA:** `Prox-AI`, `mcp-proxmox`, `ProxmoxVE`, `ProxmoxVED`, `pimox7`.
- **Asterisk / GSM / SIP:** `gsm2sip-gateway`, `asterisk`, `asterisk_v1`, `asterisk-chan-dongle`, `asterisk-chan-dongle-16`, `chan_dongle`, `AVA-AI-Voice-Agent-for-Asterisk`, `ht503-asterisk`.
- **Farming Simulator 25:** `AutoDrive_Course_Editor` e futuros mods FS25.
- **Windows / rede / utilitários:** `Activador_windows_vps`, `script_anti_ip_search`, `ip_win_bloquer`, VPN/DDNS e outras ferramentas.
