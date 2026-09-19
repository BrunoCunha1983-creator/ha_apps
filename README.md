# ha_apps

Coleção de aplicações, integrações e componentes para Home Assistant.

## Estrutura

Cada integração fica organizada em `integrations/<nome>/`.

### Integrações

- `timezone_change` — gestão de fusos horários, mudanças de hora/DST e localização móvel através de `device_tracker`.

> Este repositório funciona como monorepo de desenvolvimento. As integrações destinadas ao HACS podem ser publicadas automaticamente como repositórios independentes a partir das respetivas subpastas.
