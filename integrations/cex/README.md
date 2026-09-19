# CeX Monitor for Home Assistant

Integração não oficial para a **CeX Portugal**, organizada no monorepo `ha_apps`.

## v0.2.0 — Watchlist

A v0.2 deixa de obrigar a instalar uma entrada da integração por cada produto. Existe uma **watchlist CeX** e dentro dela podes guardar várias pesquisas e vários produtos específicos.

### Pesquisas guardadas

Cada pesquisa pode usar:

- texto livre;
- apenas produtos em stock;
- categoria(s);
- loja(s);
- raio em km a partir da localização configurada no Home Assistant;
- preço mínimo e máximo;
- preço-alvo para alertas;
- ordenação por relevância, preço, nome ou avaliação;
- ordem ascendente/descendente.

A API WSS da CeX suporta os filtros `categoryIds`, `inStock`, `storeIds`, `minPrice`, `maxPrice`, `sortBy` e `sortOrder`. Quando a pesquisa WSS é bloqueada pelo Cloudflare, a integração mantém o fallback para o site público. Nesse fallback, filtros de preço/categoria/stock são aplicados localmente quando os dados existem; o filtro de loja pode ficar indisponível.

### Produtos específicos

Também podes guardar um SKU/produto concreto e acompanhar:

- preço de venda;
- quanto a CeX paga em dinheiro;
- valor em voucher;
- stock online;
- loja mais próxima com stock;
- quantidade e distância;
- preço-alvo.

## Entidades de uma pesquisa

Cada pesquisa cria:

- `sensor.*_resultados`;
- `sensor.*_resultados_carregados`;
- `sensor.*_preco_mais_baixo`;
- `sensor.*_produto_mais_barato`;
- `sensor.*_produtos_disponiveis`;
- `sensor.*_novos_produtos`;
- `binary_sensor.*_tem_resultados`;
- `binary_sensor.*_tem_novos_produtos`;
- `binary_sensor.*_preco_alvo_atingido` quando configurado.

O sensor de resultados guarda nos atributos os primeiros 20 produtos com SKU, nome, preço, cash, voucher, stock, rating e categoria.

## Eventos para automações

A integração dispara eventos no Home Assistant depois de existir uma atualização anterior para comparação:

- `cex_new_product` — apareceu um SKU novo numa pesquisa;
- `cex_price_drop` — um produto baixou de preço;
- `cex_restock` — um produto específico voltou a ter stock online;
- `cex_target_price` — o preço passou para o valor-alvo ou abaixo.

Exemplo:

```yaml
automation:
  - alias: "CeX - novo produto"
    triggers:
      - trigger: event
        event_type: cex_new_product
    actions:
      - action: notify.mobile_app_telemovel
        data:
          title: "Novo produto na CeX"
          message: >
            {{ trigger.event.data.watch_name }}:
            {{ trigger.event.data.count }} novo(s) produto(s).
```

## Gerir a watchlist

Depois da instalação:

**Definições → Dispositivos e Serviços → CeX Monitor → Configurar**

O menu permite:

1. adicionar pesquisa guardada;
2. adicionar produto específico;
3. remover uma pesquisa/produto;
4. definir intervalo de atualização e máximo de resultados.

A alteração das opções recarrega automaticamente a integração.

## Migração da v0.1

Entradas antigas que monitorizavam um único produto são migradas automaticamente para uma watchlist com esse produto. Podem continuar a existir como entradas separadas; novas instalações usam uma única entrada **CeX Portugal**.

## Ligação à CeX

A integração tenta primeiro os endpoints WSS usados pelo site. Para pesquisa e detalhe de produto mantém o fallback browser-like para `pt.webuy.com` quando o endpoint WSS é bloqueado.

A integração não usa login, conta CeX, checkout, encomendas ou dados pessoais. É um projeto não oficial e os endpoints da CeX podem mudar sem aviso.

## Instalação manual

Copia:

`integrations/cex/custom_components/cex`

para:

`/config/custom_components/cex`

e reinicia o Home Assistant.

## HACS

A subpasta continua preparada para publicação/mirror HACS através do repositório dedicado da integração.
