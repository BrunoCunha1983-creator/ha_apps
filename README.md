# ha_apps

Monorepo principal dos projetos relacionados com **Home Assistant**.

A ideia é manter aqui o desenvolvimento organizado por tipo de projeto e evitar criar um repositório separado para cada pequena integração, cartão, automação ou componente.

## Estrutura

```text
ha_apps/
├── integrations/   # Custom integrations / custom_components
│   ├── cex/
│   └── timezone_change/
├── cards/          # Lovelace / frontend cards
├── esphome/        # Componentes externos, YAML e projetos ESPHome
├── addons/         # Add-ons para Home Assistant OS / Supervisor
├── services/       # Serviços auxiliares: bridges, Traccar/geocoder, backends
├── automations/    # Automações reutilizáveis
├── blueprints/     # Blueprints
├── packages/       # Packages Home Assistant
├── scripts/        # Scripts e ferramentas auxiliares para HA
├── dashboards/     # Dashboards / exemplos Lovelace
├── installations/  # Configurações completas Casa/Caravana
├── docs/           # Documentação e plano de migração
└── external/       # Índice de forks/projetos externos relacionados com HA
```

## Integrações atuais

- `integrations/timezone_change` — gestão de fusos horários, mudanças de hora/DST e localização móvel através de `device_tracker`.
- `integrations/cex` — monitorização de produtos CeX Portugal: preços, stock online, disponibilidade em lojas próximas e preço-alvo.

## Projetos a consolidar

O inventário completo está em [docs/MIGRATION.md](docs/MIGRATION.md).

Inclui, entre outros:
- GPSD Advanced
- GSM Tracker
- Metro Lisboa
- SIMAR
- Fogos.pt
- Ocorrências Ativas PT
- E-Redes
- Offcloud
- Resíduos PT
- Astro Tracker
- Pingo Doce Plus
- FreePBX/Asterisk bridge
- HT503
- Traccar Geocoder
- ESPHome Presence

## Regra de organização

- Projeto novo de Home Assistant criado por nós → fica neste repositório.
- Custom integration → `integrations/<domain>/`.
- Lovelace card → `cards/<nome>/`.
- ESPHome → `esphome/<nome>/`.
- Add-on → `addons/<nome>/`.
- Serviço auxiliar de HA → `services/<nome>/`.
- Automação/blueprint/package → pasta respetiva.
- Configuração completa → `installations/<nome>/`.
- Fork externo → manter referenciado em `external/` até decidirmos manter uma versão própria.

## HACS

Este repositório funciona como **monorepo de desenvolvimento**.

Projetos destinados a distribuição individual pelo HACS podem ser publicados/sincronizados para repositórios próprios a partir das respetivas subpastas. Assim conseguimos manter o GitHub organizado sem sacrificar a estrutura esperada pelas ferramentas de distribuição.


## Instalação por HACS

**Não adicionar `ha_apps` diretamente aos Repositórios personalizados do HACS.**

O HACS valida a raiz de cada repositório e uma integração HACS precisa de ter uma estrutura semelhante a:

```text
<repo>/
├── custom_components/
│   └── <domain>/
├── hacs.json
├── README.md
└── LICENSE
```

Como `ha_apps` é um monorepo, as integrações estão dentro de `integrations/<nome>/`. Por isso cada integração destinada ao HACS terá um pequeno repositório de distribuição próprio, sincronizado a partir deste monorepo.

Para as duas integrações atuais:
- `integrations/cex/` → repositório de distribuição recomendado: `ha-cex`
- `integrations/timezone_change/` → repositório de distribuição recomendado: `ha-timezone-change`

Ver [docs/HACS_DISTRIBUTION.md](docs/HACS_DISTRIBUTION.md).
