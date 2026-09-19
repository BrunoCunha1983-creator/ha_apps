# Distribuição HACS a partir do monorepo

O `ha_apps` é o repositório principal de desenvolvimento, mas o HACS não instala integrações diretamente a partir de subpastas de um monorepo.

## Motivo

Para uma custom integration, o HACS procura na raiz do repositório uma pasta `custom_components` e determina a integração a partir da primeira pasta encontrada dentro dela.

No `ha_apps`, por exemplo, a CeX está em:

```text
integrations/cex/custom_components/cex/
```

e a Timezone & Clock Change está em:

```text
integrations/timezone_change/custom_components/timezone_change/
```

Logo, adicionar URLs como `.../ha_apps/cex` ou `.../ha_apps/integrations/cex` não funciona: o HACS regista o repositório `ha_apps` e valida a raiz.

## Modelo adotado

### Desenvolvimento

```text
ha_apps/
└── integrations/
    ├── cex/
    ├── timezone_change/
    ├── gpsd_advanced/
    ├── gsm_tracker/
    └── ...
```

### Distribuição HACS

Cada integração tem um repositório pequeno cuja raiz corresponde exatamente à subpasta respetiva do monorepo.

Exemplo CeX:

```text
ha-cex/
├── custom_components/
│   └── cex/
├── hacs.json
├── README.md
└── LICENSE
```

Exemplo Timezone:

```text
ha-timezone-change/
├── custom_components/
│   └── timezone_change/
├── hacs.json
├── README.md
├── LICENSE
└── test_helpers.py
```

## Repositórios de distribuição previstos

| Pasta no monorepo | Repositório HACS |
| --- | --- |
| `integrations/cex/` | `BrunoCunha1983-creator/ha-cex` |
| `integrations/timezone_change/` | `BrunoCunha1983-creator/ha-timezone-change` |

Mais integrações serão acrescentadas à medida que forem migradas.

## Regra

O código é editado primeiro no `ha_apps`. Os repositórios HACS são apenas saídas de distribuição e não devem tornar-se cópias divergentes do código principal.
