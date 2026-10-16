---
name: loco-translate-pt
description: Traduz ficheiros .po de temas e plugins WordPress (Loco Translate) para português europeu (pt_PT), em tom formal e cordial, traduzindo apenas as strings em falta e revendo as "fuzzy". Usar sempre que o utilizador anexar ou mencionar um .po/.pot de WooCommerce, Astra, Elementor ou qualquer plugin/tema WordPress, falar de Loco Translate, "traduzir plugin", "strings por traduzir", "out of sync", ou pedir o fluxo de tradução de um site WordPress, mesmo que não diga "skill" nem "pt_PT".
---

# Tradução de temas e plugins WordPress (Loco Translate → pt_PT)

O utilizador traduz com frequência temas e plugins WordPress com o Loco Translate. O fluxo é: ele exporta o `.po`, o Claude traduz, ele importa de volta e guarda no Loco. Esta skill define o que o Claude faz e o que diz ao utilizador para fazer em cada passo.

## Princípios

- **Só português europeu (pt_PT)**, nunca pt_BR. Ver `references/glossario-pt-pt.md` para termos e ortografia.
- **Tom formal e cordial**: tratamento impessoal ou por "o seu/a sua" ("Introduza o seu email", "A sua encomenda foi registada"). Evitar "tu" e "você". Frases curtas e claras; sem gerúndio ("a processar", não "processando").
- **Só se traduz o que falta**: strings sem tradução e strings *fuzzy*. As já traduzidas ficam intactas, porque o utilizador pode tê-las afinado e porque reescrever 14 mil strings seria arriscado e desnecessário.
- **Entrega-se um `.po`** (nunca só texto). O `.mo` não se gera aqui: o Loco cria-o sozinho quando o utilizador carrega em Guardar, e é o `.mo` que o WordPress lê.

## Passo a passo para o utilizador (Loco Translate)

Explicar estes passos quando o utilizador pedir o fluxo, ou resumi-los ao entregar o ficheiro:

1. **Loco Translate → Plugins** (ou Themes) → abrir o plugin → idioma **Portuguese (Portugal)**.
2. Se o ficheiro existir só em *System* (`wp-content/languages/plugins/`), usar **Copy to Custom**. Fica em `wp-content/languages/loco/plugins/`, e **sobrevive às atualizações** do plugin. Evitar editar o ficheiro System e o da pasta do próprio plugin, porque ambos podem ser substituídos.
3. No separador **Source** ou **Editor**, correr **Sync**. O aviso "Out of sync with template" significa que o `.po` tem strings diferentes do `.pot` da versão instalada; sem Sync, as strings novas do plugin não aparecem. Guardar.
4. No Editor, **Download .po** (ícone de descarregar) e enviar o ficheiro ao Claude.
5. Receber o `.po` traduzido do Claude. Voltar ao Editor, **Import** do `.po` (ícone de engrenagem/Import) e **Guardar**. Ao guardar, o Loco gera o `.mo` na mesma pasta.
6. Confirmar no separador **File info**: o progresso deve estar perto de 100% e sem *fuzzy*. Verificar no site (limpar cache do site/objeto se houver).

Se a importação ou o Guardar falhar, a causa habitual é permissões da pasta `languages/loco/` (o Loco mostra "PO file is writeable" / "Directory is writeable" em File info; ambos devem estar verdes).

## Fluxo do Claude com o ficheiro

O script `scripts/po_tools.py` (requer `pip install --break-system-packages polib`) faz o trabalho mecânico, para que o Claude se concentre na tradução. Trabalhar sempre numa cópia do ficheiro anexado.

1. **Diagnóstico**: `python3 -I scripts/po_tools.py stats ficheiro.po`. Confirmar `Language: pt_PT` e o número de strings em falta e *fuzzy*. Se o idioma não for pt_PT, avisar o utilizador antes de continuar.
2. **Extrair em blocos**: `python3 -I scripts/po_tools.py extract ficheiro.po parte1.json --chunk 400 --part 1` (e `--part 2`, …). Blocos de ~400 strings mantêm a qualidade e cabem no contexto; um plugin grande como o WooCommerce pode ter milhares de strings, por isso trabalhar bloco a bloco e avisar o utilizador do progresso ("bloco 3 de 16").
3. **Traduzir cada bloco** para um JSON `[{"id": N, "msgstr": "..."}]`. Para plurais, `msgstr` é uma lista (`["%d artigo", "%d artigos"]`). Usar `msgctxt`, `comment` e `occurrences` para perceber o contexto (ex.: "Order" como substantivo vs. verbo). Nas *fuzzy*, comparar `current` com o original e corrigir; ao aplicar, a marca *fuzzy* é retirada automaticamente.
4. **Aplicar**: `python3 -I scripts/po_tools.py apply ficheiro.po traducoes1.json ficheiro.po` (aplicar bloco a bloco sobre o mesmo ficheiro de saída para acumular).
5. **Validar**: `python3 -I scripts/po_tools.py validate ficheiro.po`. Corrigir todos os problemas apontados (placeholders, tags HTML, entidades, espaços) e voltar a validar até ficar a zero.
6. **Entregar** com `SendUserFile`: o `.po` final, com o nome original (ex.: `woocommerce-pt_PT.po`). Dizer em duas ou três linhas quantas strings foram traduzidas/revistas e lembrar que o `.mo` é gerado ao Guardar no Loco.

## Regras técnicas de tradução

A razão destas regras: um placeholder ou tag alterado não dá erro visível no Loco, mas parte o site (texto cortado, PHP a falhar ou HTML desformatado).

- **Placeholders intactos**: `%s`, `%d`, `%1$s`, `%2$d`, `{name}`, `{{name}}`, `%name%`, `[shortcode]`. Podem mudar de ordem na frase, mas só com numeração (`%1$s`, `%2$s`); sem numeração, manter a ordem original.
- **HTML e entidades intactos**: `<a href="%s">`, `<strong>`, `&nbsp;`, `&amp;`. Traduzir apenas o texto entre tags. Não traduzir URLs, classes, atributos nem nomes de código.
- **Plurais**: pt_PT tem 2 formas (`nplurals=2; plural=(n != 1)`). Preencher `msgstr[0]` (singular) e `msgstr[1]` (plural).
- **Espaços e quebras de linha** no início/fim e `\n` têm de coincidir com o original.
- **Não traduzir**: nomes de marcas e produtos (WooCommerce, Elementor, PayPal, Stripe), códigos, nomes de funções, extensões de ficheiro, valores técnicos (`px`, `rem`, `JSON`).
- **Contexto (`msgctxt`)**: strings iguais com contextos diferentes podem exigir traduções diferentes.
- **Concisão em botões e rótulos de interface**: preferir a forma curta ("Guardar", "Eliminar", "Finalizar compra").
- **Capitalização**: seguir a regra do português (só a primeira palavra em maiúscula nos rótulos), exceto se o original for claramente título de marca.
- Na dúvida sobre uma string ambígua, escolher a leitura mais provável pelo contexto e listá-la no resumo final para o utilizador rever, em vez de interromper o trabalho.

## Casos especiais

- **Strings de JavaScript / blocos Gutenberg**: são carregadas via ficheiros `.json` que o Loco gera ao guardar, desde que o plugin use `wp_set_script_translations`. Se uma string traduzida não aparece no editor de blocos, é provavelmente este o motivo; sugerir verificar com o Loco e a cache.
- **Strings que continuam em inglês no site após guardar**: textdomain diferente do esperado, string sem `__()`/`_e()` no código, ou cache. Não é problema do `.po`.
- **Temas com tema-filho**: traduzir o tema pai (o textdomain é do pai) e guardar em *Custom*.
- **Ficheiro muito pequeno ou sem `Plural-Forms`**: acrescentar o cabeçalho `Plural-Forms: nplurals=2; plural=(n != 1);` antes de traduzir plurais.
