# CeX Monitor for Home Assistant

Integração não oficial para monitorizar produtos da **CeX Portugal** no Home Assistant.

## Funcionalidades da v0.1.1

- configuração totalmente pela UI do Home Assistant;
- pesquisa de produtos CeX durante a configuração;
- fallback automático para o site público da CeX quando o endpoint de pesquisa WSS é bloqueado;
- preço atual de venda na CeX;
- valor que a CeX paga em dinheiro;
- valor de troca/voucher;
- stock online;
- disponibilidade em lojas próximas, usando a latitude/longitude configuradas no Home Assistant;
- loja mais próxima com stock, quantidade e distância;
- `binary_sensor` de disponibilidade online e em loja;
- preço-alvo opcional com `binary_sensor` próprio;
- botão **Atualizar agora**;
- atualização automática de 30 em 30 minutos;
- imagem do produto nas entidades quando fornecida pela CeX.

## Instalação com HACS

1. Abre **HACS → Integrações**.
2. Em **Repositórios personalizados**, adiciona `BrunoCunha1983-creator/ha-cex` como **Integration**.
3. Instala/atualiza **CeX Monitor**.
4. **Reinicia o Home Assistant**.
5. Vai a **Definições → Dispositivos e Serviços → Adicionar integração** e procura **CeX Monitor**.

## Instalação manual

1. Copiar `custom_components/cex` para `/config/custom_components/cex` no Home Assistant.
2. Reiniciar o Home Assistant.
3. Abrir **Definições → Dispositivos e Serviços → Adicionar integração**.
4. Procurar por **CeX Monitor**.
5. Pesquisar o produto, selecionar o resultado e, se quiseres, indicar um preço-alvo.

Para monitorizar vários produtos, adiciona a integração novamente para cada produto.

## Entidades criadas

Por produto são criados sensores equivalentes a:

- `sensor.<produto>_preco_de_venda`
- `sensor.<produto>_valor_em_dinheiro`
- `sensor.<produto>_valor_em_voucher`
- `sensor.<produto>_stock_online`
- `sensor.<produto>_loja_mais_proxima_com_stock`
- `sensor.<produto>_stock_da_loja_mais_proxima`
- `sensor.<produto>_distancia_da_loja_mais_proxima`
- `binary_sensor.<produto>_disponivel_online`
- `binary_sensor.<produto>_disponivel_numa_loja_proxima`
- `binary_sensor.<produto>_preco_alvo_atingido` (quando configurado)
- `button.<produto>_atualizar_agora`

## Como funciona a ligação à CeX

A integração tenta primeiro os endpoints web WSS usados pela CeX. Se a pesquisa for bloqueada por proteção anti-bot/Cloudflare, a v0.1.1 tenta automaticamente a página pública `pt.webuy.com/search` e extrai os resultados server-side.

Para detalhes de produto também existe fallback para a página pública do produto. A consulta de stock de lojas continua a usar o endpoint WSS; se esse endpoint estiver temporariamente bloqueado, os restantes sensores do produto continuam a atualizar e os sensores de loja ficam sem dados até a ligação recuperar.

Não são usados login, conta CeX, checkout, encomendas ou dados pessoais.

## Diagnóstico

Se a pesquisa ainda falhar, consulta **Definições → Sistema → Registos** e procura por `CeX product search failed`. A mensagem inclui o erro do endpoint WSS e, quando aplicável, o erro do fallback do website.

## Próximos passos

- watchlists/pesquisas dinâmicas;
- alertas de novos resultados;
- histórico e variação de preço;
- filtros por raio/loja;
- ações para pesquisa e refresh;
- suporte opcional a outras regiões CeX.

