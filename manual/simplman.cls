%% 
%% A simple document class, simplman.
%% written by Nova de Hi, 2023/01/27;2023/01/29;2024/04/05.
%%
%% public domain. 
%%
%% This style requires:
%%  1. KPR package: kshcrkey
%%	2. External Fonts: Myriad Pro, Noto Sans|Serif CJK KR, HCRDotum-LVT
%%
%% Run the document with --shell-escape flag.
%%
\ProvidesClass{simplman}[2023/01/29 v2.0]

\DeclareOption*{\PassOptionsToClass{\CurrentOption}{oblivoir}}
\ProcessOptions

%%% Loads oblivoir, what a nice class!
\LoadClass[chapter,oneside,openany]{oblivoir}

%%% for tikz 'current page' node fix and \texthl command.
%%% this class does not load tikz by itself.
\RequirePackage{oblivoir-misc}

%%% page and margins
\@ifpackageloaded{fapapersize}{}{%
    \RequirePackage{fapapersize}
    \usefapapersize{210mm,297mm,2in,1in,1in,*}
}
\setmarginnotes{1.5em}{1.5in}{15pt}

%%% hyperref setting
\hypersetup{colorlinks}

%%% colors and graphics
\RequirePackage{xcolor}
\RequirePackage{graphicx}
\graphicspath{{./}{./figures}{./images}}

%%% Document Fonts
\setobmainfont(TeX Gyre Pagella)
\setobsansfont(Myriad Pro)
\setkomainfont(Noto Serif CJK KR)(* Bold)(Noto Sans CJK KR Medium)
\setkosansfont(Noto Sans CJK KR)(* Bold)(* Medium)
\setkomonofont(HANDotum-LVT.ttf)[Scale=.97]

%%% other packages to load
\RequirePackage{ragged2e}
\RequirePackage{kshcrkey} %%% KPR package
\RequirePackage{adjustbox}
\RequirePackage{pdflscape}

\RequirePackage{tcolorbox}
\tcbuselibrary{minted,breakable,skins}

\RequirePackage{efbox}
\RequirePackage{iftex}

%%% ulem: 
\ifLuaTeX
    \usepackage{memucs-interword-x}
    \AtBeginDocument{\DEFAULTskips}
    \makeatletter
    \def\@luatex@setinterhangulskip#1{} %% bug unfixed 
    \makeatother
	\compressbnms
\else %% luatexko already has its own ulem-compatible macros
\RequirePackage[normalem]{ulem}
\fi

%%% sidepar settings
\renewcommand*{\sideparform}{\RaggedRight}
\sideparmargin{left}
\newcommand*\spf{\color{gray}\hangulfontspec{Noto Sans CJK KR Light}[Ligatures=TeX]\footnotesize\selectfont}
\let\OOsidepar\sidepar
\renewcommand\sidepar[1]{\OOsidepar{\spf #1}}

%%% toc
\maxtocdepth{section}

%%% user-defined document commands and envs
\newcommand*\utt[1]{\uline{\ttfamily#1}}
\newcommand*\miktex{\texorpdfstring{MiK\TeX}{MiKTeX}}
\newcommand*\texworks{\texorpdfstring{\TeX{}works}{TeXworks}}

%%% section
\hangsecnum
\setsecnumformat{\noindent\hspace*{-.75in}\csname the#1\endcsname\quad}
\counterwithout{section}{chapter}
\counterwithin*{section}{chapter}

%%% pagestyle 'linedps': just odd-sided.
\makepagestyle{linedps}
\makeoddhead{linedps}{}{}{}
\makeoddfoot{linedps}{\sffamily\footnotesize\leftmark}{}{\sffamily\footnotesize \thepage}
\makerunningwidth{linedps}[\dimexpr\textwidth+18mm\relax]{\headwidth}
\makefootrule{linedps}{\dimexpr\textwidth+18mm\relax}{\normalrulethickness}{.5\baselineskip}
\makeheadposition{linedps}{}{}{}{flushright}
\makepsmarks{linedps}{%
	\createmark{chapter}{both}{shownumber}{}{.\space}
	\createmark{section}{right}{nonumber}{}{}
}

\aliaspagestyle{chapter}{linedps}

%%% code listing environments

%%% cmdline env.
\newtcblisting{cmdline}[1][bash]{%
	colback=blue!15,
	colframe=green!50!black,
	listing only,
	drop fuzzy shadow,
	hbox,enhanced,
	before=\begin{center},
	after=\end{center},
	minted language=#1
}

%%% texsnip env.
\newtcblisting{texsnip}{%
	colback=gray!8,
	colframe=black,
	listing only,
	leftrule=0pt,rightrule=0pt,
	minted options={baselinestretch=1.05}
}

%%% Chamgo environment
%%% \begin{Chamgo} ... \end{Chamgo}
\def\chamgomarktitle{참고}
\newcommand*\chamgo{\efbox[%
	backgroundcolor=gray!95,%
	leftline=false,%
	rightline=false,%
	linewidth=1.5pt,%
	font=\color{white}\sffamily\bfseries\footnotesize
  ]{\chamgomarktitle}}
\colorlet{shadecolor}{gray!10}
\newenvironment{Chamgo}[1][참고]{%
	\renewcommand*\chamgomarktitle{#1}
	\begin{snugshade}
	\noindent\chamgo\space
}{%
	\end{snugshade}
}

%%% TitlePage environment
\newenvironment{TitlePage}{%
	\titlingpageend{\clearpage}{\clearpage}
	\begin{titlingpage}
	\calccentering{\unitlength}
	\begin{adjustwidth*}{\unitlength}{-\unitlength}
}{%
	\end{adjustwidth*}
	\end{titlingpage}
}

%%% activate chapterstyle and pagestyle 
\AtBeginDocument{%
	\chapterstyle{obmadsen}
	\pagestyle{linedps}
}

%%% rightclick
\NewDocumentCommand \RightClick {}
{
	{%
		\setlength\fboxsep{1pt}%
		\fbox{\footnotesize Right Click}%
	}%
}

\endinput
