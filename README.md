# skills

As minhas skills pessoais para agentes de IA (Claude Code, etc.).

## Instalar

Todas as skills:

```bash
bunx --bun skills add luisguerra293/skills -g
```

Uma skill específica:

```bash
bunx --bun skills add luisguerra293/skills --skill woocommerce-csv-import -g
```

## Skills

| Skill | Descrição |
|-------|-----------|
| [woocommerce-csv-import](skills/woocommerce-csv-import/SKILL.md) | Importar, atualizar e resolver problemas de CSV de produtos no WooCommerce |

## Adicionar uma nova skill

Criar `skills/<nome-da-skill>/SKILL.md` com cabeçalho YAML (`name`, `description`), fazer commit e push.
