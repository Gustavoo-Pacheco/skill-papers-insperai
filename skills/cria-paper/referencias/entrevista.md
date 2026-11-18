# Roteiro de entrevista da cria-paper

Quando falta informação, a skill **pergunta antes de escrever**. Ela não preenche lacunas com suposições nem deixa TODOs para depois.

## Regras

- Rodadas curtas, de até 4 perguntas, com opções quando der. Use a ferramenta interativa no Claude Code e o chat no app.
- Comece pelo que muda mais o paper: o problema, a contribuição principal e os resultados que existem.
- Não pergunte o que o material já responde. Mostre o que encontrou ("o notebook dá AUC 0,742 no conjunto X; é esse o resultado principal?") e peça confirmação.
- Sem resultados: pergunte se o paper espera os experimentos ou descreve só o método e o plano. Nunca invente números.
- Registre tudo em `trabalho/entrevista.md`. Toda afirmação do paper que não vem de um arquivo vem dali.

## Perguntas-modelo por seção

| Seção | O que precisa existir antes de escrever | Perguntas-modelo |
|---|---|---|
| Capa | Título, autores, data | "Quem são os autores, na ordem?" · "Título provisório: [proposta]. Serve?" |
| Introdução | O problema, por que importa e a contribuição principal | "Qual problema o projeto resolve, em uma frase?" · "Qual é a contribuição principal: [opção A do repo], [opção B] ou outra?" |
| Trabalhos relacionados | Os trabalhos que o grupo usou como base, com referências reais | "Em que trabalhos o projeto se baseou? Achei estes no README: [lista]. Falta algum?" |
| Método | O que foi feito: dados, modelo, protocolo, métricas | "O dataset é [X do repo]. A divisão treino/teste foi [Y]?" · "Qual config gerou o resultado final: [arquivo A] ou [arquivo B]?" |
| Resultados | Os números finais e a origem de cada um | "Qual é o resultado principal: [tabela/célula do notebook]?" · "Esse número é a média de quantas sementes?" |
| Limitações | O que não funcionou, não foi testado ou não generaliza | "O que não funcionou ou ficou de fora?" · "Em que cenário os resultados não valem?" |
| Código e dados | URL, commit ou tag, dados, licença | "Este é o repositório final: [URL], commit [hash]?" · "Os dados podem ser redistribuídos?" |
| Conclusão | O que o leitor deve levar e os próximos passos | "Qual é a mensagem principal?" · "Quais são os próximos passos?" |

## Ordem sugerida das rodadas

1. Problema, contribuição principal, resultado principal e autores.
2. Método e dados: só o que o repo não deixou claro.
3. Trabalhos relacionados e referências.
4. Limitações, código e dados, próximos passos.
