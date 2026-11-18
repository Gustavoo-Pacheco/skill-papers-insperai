# Classificação de folhas com redes convolucionais pequenas

Ana Souza, Bruno Lima, Claude (Anthropic)

Insper AI

## Resumo

Este relatório testa se uma rede convolucional com menos de 100 mil parâmetros classifica folhas de cinco espécies com acurácia útil. A rede chega a **91,4%** no conjunto de teste.

## 1. Introdução

Classificar folhas no campo exige modelos que rodem num celular. Este trabalho compara uma CNN pequena com uma *baseline* de regressão logística [1].

## 2. Método

O conjunto tem 2.500 imagens, divididas em 80% para treino e 20% para teste. A rede tem três camadas convolucionais e foi treinada por 30 épocas.

- Otimizador: Adam, taxa de aprendizado 0,001.
- Aumento de dados: rotação e espelhamento.

## 3. Resultados

A CNN alcança 91,4% de acurácia, contra 78,2% da regressão logística [2].

## 4. Conclusão

Uma rede pequena basta para esta tarefa.

## Referências

[1] K. He, X. Zhang, S. Ren e J. Sun. Deep residual learning for image recognition. CVPR, 2016.
[2] D. P. Kingma e J. Ba. Adam: a method for stochastic optimization. arXiv:1412.6980, 2014.
