# Changelog

As versões seguem o formato x.y.z (versionamento semântico):

- **x:** mudança no padrão que deixa papers antigos fora do padrão, como uma seção nova obrigatória ou outro layout.
- **y:** recurso novo compatível com o que já existe.
- **z:** correção.

Cada versão vira uma Release no GitHub, com os `.zip` de `dist/` anexados.

## [Não lançado]

### Alterado
- Capa: título, autores e resumo no estilo de *Attention Is All You Need* (título entre filetes, autores em blocos centralizados, resumo centralizado e recuado), no lugar do título à esquerda e do resumo em caixa.

### Adicionado
- Scaffold do projeto: `padrao/`, as três skills, `build.py`, testes e docs.
- Análise de 39 papers de referência em `docs/referencias.md`.
- Classe `insperai.cls` (capa com logo, resumo destacado, legendas "Figura N | Título.", `\linhadestaque`, `\secaofaltando`, `\notacapa`) e estilos de bibliografia em português.
- Paleta de gráficos validada para daltonismo em `insperai.mplstyle`.
- Scripts: `extrair_entrada.py` (PDF, .docx, Markdown, .tex), `montar_latex.py`, `completar_bib.py`, `compilar.sh`, `verificar_texto.py`, `verificar_checklist.py`, `contar_palavras.py`, `inventario_repo.py`, `recortar_figuras.py`.
- Testes: caso Wakely, caso sintético com autor IA, prompts e `tests/rodar_teste_skill.sh` para rodar as skills sem interface, `tests/verificar_cobertura.py`.
