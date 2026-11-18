% insperai.cls: classe do relatório técnico do Insper AI
% Decisões em padrao/estrutura.md e padrao/guia-de-estilo.md. Compila com Tectonic (XeTeX) e no Overleaf.
%
% Opções:  portugues (padrão) | english      autorano (padrão) | numerico
% Capa (estilo Attention Is All You Need):    \title{...} \subtitulo{...} \author{A \and B; \AND força nova linha} \afiliacao{...} \email{...} \data{...} \resumo{...}
% Legenda: \legenda{Título}{Descrição}  ->  "Figura N | Título. Descrição"
% Tabela:  \linhadestaque antes da linha do método proposto
% Seção obrigatória ausente: \secaofaltando{Limitações}
% Nota da capa (linhas da capa original que o padrão não tem): \notacapa{...}
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{insperai}[2026/11/18 v1.0 Relatorio tecnico do Insper AI]

\newif\ifinsper@english
\newif\ifinsper@numerico
\DeclareOption{english}{\insper@englishtrue}
\DeclareOption{portugues}{\insper@englishfalse}
\DeclareOption{numerico}{\insper@numericotrue}
\DeclareOption{autorano}{\insper@numericofalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[a4paper,10pt,twocolumn]{article}

% ---------- Motor, idioma e fontes ----------
\RequirePackage{iftex}
\ifPDFTeX
  \RequirePackage[T1]{fontenc}
  \RequirePackage[utf8]{inputenc}
\else
  \PassOptionsToPackage{no-math}{fontspec}% dígitos da matemática em XCharter, não em Latin Modern
\fi
\ifinsper@english
  \RequirePackage[english]{babel}
\else
  \RequirePackage[brazilian]{babel}
\fi
\RequirePackage{amsmath}
\RequirePackage[xcharter,vvarbb]{newtxmath}
\RequirePackage{XCharter}
\RequirePackage{microtype}

% ---------- Página ----------
\RequirePackage[a4paper,top=2cm,bottom=2.2cm,left=1.8cm,right=1.8cm,columnsep=0.6cm]{geometry}
\setlength{\parindent}{1em}
\setlength{\parskip}{0pt}
\renewcommand{\tableofcontents}{\ClassWarning{insperai}{O padrao do Insper AI nao usa sumario; \protect\tableofcontents ignorado}}

% ---------- Cores do lab ----------
\RequirePackage[table]{xcolor}
\definecolor{insperCobalto}{HTML}{0058B8}
\definecolor{insperAzul}{HTML}{016FD0}
\definecolor{insperMagenta}{HTML}{B128C0}
\definecolor{insperMagentaMedio}{HTML}{D86FE0}
\definecolor{insperNoite}{HTML}{1E2A44}
\definecolor{insperCinza}{HTML}{A3A8B0}
\definecolor{insperTextoSuave}{HTML}{4B5563}

% ---------- Figuras, tabelas, listas ----------
\RequirePackage{graphicx}
\graphicspath{{figuras/}}
\RequirePackage{booktabs,multirow,tabularx,array}
\RequirePackage{enumitem}
\setlist{nosep,leftmargin=*}
\RequirePackage{caption}
\RequirePackage{subcaption}
\DeclareCaptionLabelSeparator{barra}{\ \textbar\ }
\captionsetup{labelfont=bf,labelsep=barra,font=small,justification=justified,singlelinecheck=false}
\newcommand{\legenda}[2]{\caption{\textbf{#1} #2}}
\newcommand{\linhadestaque}{\rowcolor{insperCobalto!10}}

% ---------- Títulos de seção (pretos) ----------
\RequirePackage{titlesec}
\titleformat{\section}{\normalfont\large\bfseries}{\thesection}{0.6em}{}
\titleformat{\subsection}{\normalfont\normalsize\bfseries}{\thesubsection}{0.6em}{}
\titleformat{\subsubsection}{\normalfont\normalsize\bfseries\itshape}{\thesubsubsection}{0.6em}{}
\titlespacing*{\section}{0pt}{1.4ex plus .4ex minus .2ex}{0.8ex}
\titlespacing*{\subsection}{0pt}{1.1ex plus .3ex minus .2ex}{0.5ex}
\titleformat{\paragraph}[runin]{\normalfont\normalsize\bfseries}{}{0pt}{}
\titlespacing*{\paragraph}{0pt}{0.8ex plus .3ex}{0.6em}

% ---------- Citações ----------
% Em português usa insperai-*-pt.bst ("e", "Em", "páginas"); em inglês, os estilos originais do natbib.
\ifinsper@numerico
  \RequirePackage[numbers,sort&compress]{natbib}
  \ifinsper@english\AtBeginDocument{\bibliographystyle{unsrtnat}}\else\AtBeginDocument{\bibliographystyle{insperai-numerico-pt}}\fi
\else
  \RequirePackage[authoryear,round]{natbib}
  \ifinsper@english\AtBeginDocument{\bibliographystyle{plainnat}}\else\AtBeginDocument{\bibliographystyle{insperai-autorano-pt}}\fi
\fi
\setlength{\bibsep}{2pt plus 1pt}
\renewcommand{\bibfont}{\small}

% ---------- Links (Azul Cobalto) ----------
\RequirePackage{xurl}
\RequirePackage[colorlinks=true,linkcolor=insperCobalto,citecolor=insperCobalto,urlcolor=insperCobalto,breaklinks=true]{hyperref}

% ---------- Capa ----------
\newcommand{\insper@subtitulo}{}
\newcommand{\insper@afiliacao}{Insper AI, Insper}
\newcommand{\insper@email}{contato@insperai.com.br}
\newcommand{\insper@data}{\today}
\newcommand{\insper@logo}{logo-insperai.png}
\newcommand{\insper@resumo}{}
\newcommand{\insper@notacapa}{}
\newcommand{\notacapa}[1]{\renewcommand{\insper@notacapa}{#1}}% linhas extras da capa original (formata)
\newcommand{\subtitulo}[1]{\renewcommand{\insper@subtitulo}{#1}}
\newcommand{\afiliacao}[1]{\renewcommand{\insper@afiliacao}{#1}}
\newcommand{\email}[1]{\renewcommand{\insper@email}{#1}}
\newcommand{\data}[1]{\renewcommand{\insper@data}{#1}}
\newcommand{\logo}[1]{\renewcommand{\insper@logo}{#1}}
\newcommand{\resumo}[1]{\renewcommand{\insper@resumo}{#1}}
\ifinsper@english
  \newcommand{\insper@resumoname}{Abstract}
  \newcommand{\insper@faltandoname}{MISSING SECTION}
  \newcommand{\insper@faltandotexto}{This section is required by the Insper AI standard and was not in the original paper.}
\else
  \newcommand{\insper@resumoname}{Resumo}
  \newcommand{\insper@faltandoname}{SEÇÃO FALTANDO}
  \newcommand{\insper@faltandotexto}{Esta seção é obrigatória no padrão do Insper AI e não existia no paper original.}
\fi

\renewcommand{\maketitle}{%
  % Título, autores e resumo no estilo de "Attention Is All You Need" (NeurIPS):
  % título centralizado entre filetes, autores em blocos centralizados, resumo centralizado e recuado.
  \twocolumn[{%
    \begingroup
    \noindent
    \begin{minipage}[c]{0.5\textwidth}\includegraphics[height=1.0cm]{\insper@logo}\hspace{0.2cm}%
      \raisebox{0.32cm}{\large\bfseries\color{insperNoite}Insper AI}\end{minipage}%
    \begin{minipage}[c]{0.5\textwidth}\raggedleft\small\color{insperTextoSuave}\insper@data\end{minipage}\par
    \vspace{0.4cm}%
    \centering
    \hrule height 4pt
    \vskip 0.25in
    {\LARGE\bfseries\@title\par}%
    \ifx\insper@subtitulo\@empty\else
      \vskip 0.1in{\large\insper@subtitulo\par}%
    \fi
    \vskip 0.29in
    \hrule height 1pt
    \vskip 0.09in
    \def\and{\end{tabular}\hfil\linebreak[0]\hfil\begin{tabular}[t]{c}\bfseries\rule{\z@}{24\p@}\ignorespaces}%
    \let\And\and
    \def\AND{\end{tabular}\hfil\linebreak[4]\hfil\begin{tabular}[t]{c}\bfseries\rule{\z@}{24\p@}\ignorespaces}%
    \begin{tabular}[t]{c}\bfseries\rule{\z@}{24\p@}\@author\end{tabular}\par
    \vskip 0.08in
    {\normalsize\insper@afiliacao\par}%
    {\normalsize\href{mailto:\insper@email}{\texttt{\insper@email}}\par}%
    \ifx\insper@notacapa\@empty\else
      \vspace{0.12cm}{\footnotesize\color{insperTextoSuave}\insper@notacapa\par}%
    \fi
    \ifx\insper@resumo\@empty\else
      \vskip 0.3in
      {\large\bfseries\insper@resumoname\par}%
      \vspace{0.5ex}%
      \parbox{0.8\textwidth}{\setlength{\parskip}{0.35em}\insper@resumo}\par
    \fi
    \vspace{0.6cm}%
    \endgroup
  }]%
}

% ---------- Seção obrigatória ausente ----------
\newcommand{\secaofaltando}[1]{%
  \section{#1}%
  \noindent\fcolorbox{insperMagenta}{insperMagenta!8}{\parbox{\dimexpr\linewidth-2\fboxsep-2\fboxrule\relax}{%
    \textbf{[\insper@faltandoname: #1]} \insper@faltandotexto}}\par}

\pagestyle{plain}
\endinput
