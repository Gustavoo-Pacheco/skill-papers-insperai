# Checklist final do Insper AI

> Fonte única. As três skills rodam este checklist antes de entregar e listam no resumo da entrega o que não passou.
> Os itens (auto) são conferidos por `scripts/verificar_checklist.py <pasta> --skill formata|refaz|cria`. Os outros, a skill confere lendo o PDF.

## Forma
- [ ] (auto) Usa a classe `insperai.cls`: A4, duas colunas, Charter.
- [ ] Capa com o logo e a data; título, autores e resumo no estilo de *Attention Is All You Need* (título centralizado entre filetes, autores em blocos centralizados, afiliação e e-mail do lab, contato@insperai.com.br, e resumo centralizado e recuado).
- [ ] (auto) Nenhuma IA na lista de autores. Se havia, foi removida e avisada.
- [ ] (auto) Todas as seções obrigatórias de `estrutura.md` existem, com o título do padrão, uma seção para cada e na ordem certa. Na formata, desvios são avisos: ela mantém a ordem e a numeração originais.
- [ ] (auto) Não há sumário.
- [ ] (auto) Legendas pelo `\legenda{Título.}{Descrição}` ("Figura N | **Título.** Descrição").
- [ ] (auto) Tabelas sem linhas verticais. Tabelas recompostas usam booktabs.
- [ ] Gráficos gerados pela skill usam `insperai.mplstyle`. Com mais de 4 séries, também marcadores ou tipos de linha.
- [ ] (auto) Todos os caracteres têm glifo na fonte (nada em branco no PDF).

## Conteúdo
- [ ] (auto) A seção "Código e dados" tem um parágrafo só, com onde, o quê, dados e licença.
- [ ] A seção "Limitações" existe e não é genérica.
- [ ] (auto) Resumo de 150 a 250 palavras (recomendado; aviso, não falha).
- [ ] Contribuições num parágrafo no fim da introdução (refaz e cria).
- [ ] Redação impessoal, presente para o que o paper faz e passado para os experimentos (refaz e cria).
- [ ] (formata) (auto) Texto idêntico ao da entrada: `scripts/verificar_texto.py` termina em TEXTO IDÊNTICO.
- [ ] (refaz) Todo número vem do repositório ou do paper original, e cada divergência foi perguntada e registrada.
- [ ] (refaz) (auto) Tamanho dentro de ±10% das palavras do corpo do original: `scripts/contar_palavras.py`.
- [ ] (cria) Nenhum resultado inventado. Todo número tem origem em `trabalho/fontes.md` ou nas respostas da entrevista.

## Referências
- [ ] (auto) Toda citação existe no `refs.bib`.
- [ ] Entradas confirmadas e completadas pelo arXiv, Crossref, DataCite, OpenAlex ou Semantic Scholar. As não confirmadas estão marcadas `[VERIFICAR]` e listadas no resumo.
- [ ] (auto) Estilo de citação único no documento todo (definido pela opção da classe).

## Entrega
- [ ] Pasta `<nome-do-paper>-insperai/` com `main.tex`, `refs.bib`, `figuras/` e `main.pdf`, conforme o formato pedido.
- [ ] (auto) O PDF compilou com Tectonic e está atualizado. Se não compilou, o usuário foi avisado e recebeu o .tex pronto para o Overleaf.
- [ ] O resumo da entrega lista as mudanças, os avisos e os itens `[VERIFICAR]`.
