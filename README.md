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
├── automations/    # Automações reutilizáveis
├── blueprints/     # Blueprints
├── packages/       # Packages Home Assistant
├── scripts/        # Scripts e ferramentas auxiliares para HA
├── dashboards/     # Dashboards / exemplos Lovelace
├── docs/           # Documentação e plano de migração
└── external/       # Índice de forks/projetos externos relacionados com HA
```

## Integrações atuais

- `integrations/timezone_change` — gestão de fusos horários, mudanças de hora/DST e localização móvel através de `device_tracker`.
- `integrations/cex` — monitorização de produtos CeX Portugal: preços, stock online, disponibilidade em lojas próximas e preço-alvo.

## Regra de organização

- Projeto novo de Home Assistant criado por nós → fica neste repositório.
- Custom integration → `integrations/<domain>/`.
- Lovelace card → `cards/<nome>/`.
- ESPHome → `esphome/<nome>/`.
- Add-on → `addons/<nome>/`.
- Automação/blueprint/package → pasta respetiva.
- Fork externo que queremos acompanhar → não é misturado cegamente com o nosso código; fica referenciado em `external/` ou é importado apenas quando decidirmos manter uma versão própria.

## HACS

Este repositório funciona como **monorepo de desenvolvimento**.

Projetos destinados a distribuição individual pelo HACS podem ser publicados/sincronizados para repositórios próprios a partir das respetivas subpastas. Assim conseguimos manter o GitHub organizado sem sacrificar a estrutura esperada pelas ferramentas de distribuição.

## Migração

O inventário dos repositórios antigos e o respetivo destino está em [docs/MIGRATION.md](docs/MIGRATION.md).
