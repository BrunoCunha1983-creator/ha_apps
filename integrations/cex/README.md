# CeX Monitor for Home Assistant

Integração não oficial para monitorizar produtos da **CeX Portugal** no Home Assistant.

## Funcionalidades da v0.1.0

- configuração totalmente pela UI do Home Assistant;
- pesquisa de produtos CeX durante a configuração;
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

O nome final das entidades é atribuído pelo Home Assistant e pode ser alterado na UI.

## API

Esta integração usa os endpoints web públicos utilizados pelo site CeX/WeBuy (`wss2.cex.pt.webuy.io`). Não existe afiliação oficial com a CeX e estes endpoints podem mudar sem aviso.

Não são usados login, conta CeX, checkout, encomendas ou dados pessoais.

## Próximos passos

- watchlists/pesquisas dinâmicas;
- alertas de novos resultados;
- histórico e variação de preço;
- filtros por raio/loja;
- ações para pesquisa e refresh;
- suporte opcional a outras regiões CeX.
