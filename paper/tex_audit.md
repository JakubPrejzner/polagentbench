# tex_audit.md — audyt źródeł LaTeX i kompilacji

**Data wygenerowania:** 2026-08-23
**Repo:** `polagentbench`, branch `main`, HEAD `6c4f241`

---



<!-- source section: 06_tex_audit.md -->

## Audyt zrodel .tex (KROK 1) i kompilacja (KROK 4)

Data wykonania: 2026-08-23. Repo `C:\Users\japre\polagentbench` @ `6c4f241a54ef5e944513e7a020923764f4dcd983`, branch `main` — nie modyfikowane (praca wylacznie do odczytu). Wszystkie zapisy poszly do `...\scratchpad\` (kopie robocze .tex, logi kompilacji, skrypty pomocnicze).

---

### DWIE KOREKTY DO "FAKTOW USTALONYCH"

Zglaszam je na wstepie, bo zmieniaja zakres KROKU 4 i obraz stanu papieru.

**KOREKTA 1 — pdflatex JEST zainstalowany.** Kontekst mowil "pdflatex NIE jest zainstalowany na tej maszynie". Na dysku jest **TinyTeX** (`C:\Users\japre\AppData\Roaming\TinyTeX`, katalog utworzony 2026-08-22 05:23), z pelnym `pdflatex.exe`:

```
$ /c/Users/japre/AppData/Roaming/TinyTeX/bin/windows/pdflatex.exe --version
pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026)
kpathsea version 6.4.2
```

Powodem, dla ktorego wczesniejsze sprawdzenie dalo negatywny wynik, jest to, ze **TinyTeX nie jest w PATH** — `which pdflatex` i `Get-Command pdflatex` zwracaja "BRAK". Trzeba wolac po pelnej sciezce. Konsekwencja: KROK 4 wykonalem jako **realna kompilacje**, nie jako analize statyczna (sekcja CZESC 6). W samym scratchpadzie leza zreszta `install-tinytex.bat` i `install_tinytex.ps1` z 2026-08-23 03:06 — instalacja jest artefaktem tej samej linii pracy.
Zrodlo: `ls /c/Users/japre/AppData/Roaming/TinyTeX/bin/windows` (81 plikow .exe, w tym `pdflatex.exe`, `xelatex.exe`, `lualatex.exe`, `latexmk.exe`, `bibtex.exe`, `kpsewhich.exe`, `tlmgr.bat`).

**KOREKTA 2 — istnieje trzeci artefakt draftu, ktorego kontekst nie wymienial: `polagentbench_paper.pdf`.** To **skompilowany, 10-stronicowy draft z 2026-07-24** o tytule *"Quantization Thresholds Are Universal, Failure Modes Are Not: A Cross-Model Study of Agentic Tool Use in Polish from 8-bit to 2-bit"*. **Nie jest** to papier docelowy (inny tytul, DWA modele zamiast trzech, zero wystapien slowa "PLLuM"), ale jest najblizszym istniejacym pelnym draftem i zawiera juz sekcje "Finding 3", drabine L0-L3 i material o repair. Jego **zrodla .tex nie ma nigdzie na dyskach C: ani D:** — na dysku jest wylacznie PDF. To nie obala tezy "papieru docelowego nie ma jako .tex", ale zmienia jej sens: brakuje nie tylko papieru docelowego, ale i zrodel jego bezposredniego poprzednika.

---

### CZESC 1 — Poszukiwanie papieru docelowego

#### 1.1 Wykonane komendy i ich wyniki

| # | Komenda | Wynik |
|---|---------|-------|
| 1 | `find /c/Users/japre -maxdepth 6 -iname "*.tex" ...` | 5 plikow (lista nizej) |
| 2 | `find /c/Users/japre -path /c/Users/japre/AppData -prune -o \( -iname "*.tex" -o -iname "*.bib" -o -iname "*.bbl" -o -iname "*.cls" -o -iname "*.sty" \) -print` | te same 5 plikow, **zero** .bib/.bbl/.cls/.sty |
| 3 | `find /c -maxdepth 8 ... \( -iname "*.tex" -o -iname "*.bib" -o -iname "*.bbl" \) -print` (z pominieciem Windows, Program Files, ProgramData, $Recycle.Bin, System Volume Information, AppData) | te same 5 plikow |
| 4 | `find /d -maxdepth 7 \( -iname "*.tex" -o -iname "*.bib" -o -iname "*.bbl" \)` (dysk D:, 801 GB uzyte) | **0 wynikow** |
| 5 | `find ... -maxdepth 5 -type d \( -iname "*paper*" -o -iname "*arxiv*" -o -iname "*submission*" -o -iname "*draft*" -o -iname "*manuscript*" -o -iname "*preprint*" \)` na `/c/Users/japre`, `/c/PROJEKTY`, `/c/moje projekty` | 2 trafienia, oba nie na temat: `/c/Users/japre/.lmstudio/.internal/config-presets-drafts`, `/c/moje projekty/arxiv-mcp-server` (klon serwera MCP, bez .tex) |
| 6 | `find /d -maxdepth 5 -type d \( -iname "*paper*" -o -iname "*arxiv*" -o -iname "*polagent*" \)` | 2 trafienia: `/d/TEST OCR/ocr_study/deliverables/paper`, `/d/TEST OCR/ocr_study_review/deliverables/paper` — zawieraja wylacznie `OCR_Study_Paper_{EN,PL}.{docx,pdf}`, temat OCR, bez zwiazku |
| 7 | `find /c/Users/japre/AppData \( -iname "*.tex" -o -iname "*.bib" \)` | tylko dokumentacja Ghostscript, drzewo TinyTeX (`texmf-dist/...`) oraz **`AppData/Roaming/Cursor/User/History/6ac45d2/KIIh.tex`** |
| 8 | `cat .../Cursor/User/History/6ac45d2/entries.json` | `{"resource":"file:///c%3A/Users/japre/Desktop/bielik_q2_sharp.tex", ...}` — to kopia historii edytora TEGO SAMEGO pliku, md5 identyczny z Desktopowym |
| 9 | `find ... \( -iname "*.zip" -o -iname "*.tar.gz" -o -iname "*.tgz" \) \( -iname "*paper*" -o -iname "*arxiv*" -o -iname "*overleaf*" -o -iname "*cliff*" -o -iname "*polagent*" -o -iname "*bielik*" \)` | **0 wynikow** (brak tarballa/paczki Overleaf) |
| 10 | `git log --all --diff-filter=A --name-only --pretty=...` w repo (245 linii, 53 commity, branche: `main`, `origin/main`) → `grep -icE "\.(tex\|bib\|bbl\|sty\|cls)$"` | **0** |
| 11 | `git rev-list --objects --all \| grep -icE "\.(tex\|bib\|bbl\|sty\|cls)$"` (493 obiekty) | **0** |
| 12 | `find . -maxdepth 3 -type d \( -iname "*paper*" -o -iname "*arxiv*" -o -iname "*draft*" -o -iname "*submission*" -o -iname "*tex*" \)` w repo | **0 wynikow** |

#### 1.2 Grep fraz kluczowych

Komenda: `grep -ril --include="*.tex" --include="*.bib" --include="*.md" --include="*.txt" -- "<FRAZA>"` po `/c/Users/japre/{Desktop,Downloads,Documents,polagentbench,OneDrive}`, `/c/moje projekty`, `/c/PROJEKTY`.

| Fraza | Trafienia |
|-------|-----------|
| `Q2 Cliff` | `polagentbench/results/v3_full_2026-06-02/CURVE.md`, `polagentbench/SESSION_LOG.md` |
| `Agentic Degradation` | `polagentbench/SESSION_LOG.md` (tylko) |
| `GGUF Quantization` | `Desktop/bielik_q2_sharp.tex`, `Downloads/bielik_q2_sharp (1).tex`, `Downloads/bielik_q2_sharp.tex`, `polagentbench/SESSION_LOG.md` |
| `Three Polish` | `polagentbench/SESSION_LOG.md` (tylko) |
| `polagentbench` | 9 plikow w repo + `/c/PROJEKTY/BitSHARPv2/DESIGN-LOG.md` + wpis w `.venv/.../entry_points.txt` |

Pelen tytul docelowy wystepuje **wylacznie** w `polagentbench/SESSION_LOG.md:645`:

> `- **Tytuł papera:** „The Q2 Cliff: Agentic Degradation Under GGUF Quantization in Three Polish`
> `  Open Models".`

W plikach .tex fraza `Q2 Cliff` ma **0** wystapien (skrypt `scratchpad/kw.py`, wejscie: oba .tex).

#### 1.3 Grep w .docx / .pdf

`find ... \( -iname "*.pdf" -o -iname "*.docx" \) \( -iname "*paper*" -o -iname "*arxiv*" -o -iname "*cliff*" -o -iname "*quant*" -o -iname "*bielik*" -o -iname "*agent*" -o -iname "*polagent*" -o -iname "*draft*" -o -iname "*preprint*" \)` → 37 plikow. Istotne dwa (tekst wyciagniety `pdftotext`, dostepnym w `/mingw64/bin/pdftotext`):

- `Desktop/polagentbench_paper.pdf` (228 459 B, 2026-07-25 00:51; md5 `89c0987eb290a0923dc3e107716e8703` — identyczny z 4 kopiami w Downloads i 1 dodatkowa na Desktopie, razem 6 identycznych kopii) — 10 stron, data na stronie tytulowej `July 24, 2026`.
- `Downloads/PolAgentBench_preview.pdf` (249 876 B, 2026-05-03 02:03) — 5 stron, `May 3, 2026`, tytul *"PolAgentBench: Quantization and Language-Interface Failures in Polish Tool-Using LLM Agents"*, oznaczony "Work in progress — preliminary results".

Zaden z nich nie nosi tytulu docelowego. `grep -i -F "Q2 Cliff"` w obu wyciagach tekstu → **0**. `PLLuM` w `polagentbench_paper.pdf` → **0 wystapien** (skrypt `scratchpad/kw.py`, wejscie `scratchpad/pdftxt/polagentbench_paper_full.txt`).

#### 1.4 WERDYKT CZESCI 1

**POTWIERDZAM brak papieru docelowego.** Na dyskach C: i D: nie istnieje zaden plik `.tex`, `.bib`, `.bbl`, `.sty` ani `.cls` zawierajacy tytul „The Q2 Cliff: Agentic Degradation Under GGUF Quantization in Three Polish Open Models" ani opisujacy trzy modele. Tytul zyje wylacznie jako jedna linia decyzji w `SESSION_LOG.md:645`. Historia gita repo nigdy nie zawierala pliku TeX-owego (0 z 493 obiektow, 0 z 245 wpisow `--diff-filter=A`).

**Pelna lista plikow .tex na maszynie (5 sztuk, 3 unikalne tresci):**

| Sciezka | Rozmiar | Linie | Data | md5 |
|---------|---------|-------|------|-----|
| `C:\Users\japre\Desktop\bielik_q2_sharp.tex` | 53 035 B | 744 | 2026-03-05 11:35 | `1c9b998a1f31b19ffef994bec4204263` |
| `C:\Users\japre\AppData\Roaming\Cursor\User\History\6ac45d2\KIIh.tex` | 53 035 B | 744 | 2026-03-05 11:35 | `1c9b998a…` (identyczny z powyzszym) |
| `C:\Users\japre\Downloads\bielik_q2_sharp (1).tex` | 53 010 B | 744 | 2026-03-04 16:08 | `c01d433b23d036185cb2ca1584929193` (2 linie roznicy vs Desktop) |
| `C:\Users\japre\Downloads\bielik_q2_sharp.tex` | 52 913 B | 744 | 2026-03-03 15:37 | `ed16add22fb0be53f01fc2bf62ab8572` (8 linii roznicy vs Desktop) |
| `C:\Users\japre\Desktop\results_section.tex` | 7 095 B | 143 | 2026-06-02 21:52 | `b8765d82b2982c64ab9d530fbec0c87f` |
| `C:\Users\japre\Downloads\results_section.tex` | 7 095 B | 143 | 2026-06-02 21:52 | `b8765d82…` (identyczny) |

Wszystkie trzy warianty `bielik_q2_sharp` maja ten sam `\title` (linia 23). Audytuje wersje **Desktopowa** jako najnowsza.

**Brak plikow .bib na calej maszynie** (poza `TinyTeX/texmf-dist/bibtex/bib/base/xampl.bib`, ktory jest przykladem z dystrybucji TeX-a). Brak plikow `.bbl`.

---

### CZESC 2 — Drzewo sekcji z numerami linii

Skrypt zrodlowy: `scratchpad/texstruct.py` (napisany na potrzeby tego audytu; wypisuje kazda linie zawierajaca jedna z 33 komend strukturalnych LaTeX-a).

#### 2.1 `C:\Users\japre\Desktop\bielik_q2_sharp.tex` (744 linie)

```
    1  \documentclass[11pt,a4paper]{article}
    3  \usepackage[utf8]{inputenc}
    4  \usepackage[T1]{fontenc}
    5  \usepackage{amsmath,amssymb,amsfonts}
    6  \usepackage{graphicx}
    7  \usepackage{booktabs}
    8  \usepackage{hyperref}
    9  \usepackage{url}
   10  \usepackage{natbib}
   11  \usepackage{geometry}
   12  \usepackage{xcolor}
   23  \title{Bielik-Q2-Sharp: A Comparative Study of Extreme 2-bit\\Quantization Methods for a Polish 11B Language Model}
   25  \author{Jakub Prejzner\textsuperscript{1}\\
   26     \textsuperscript{1}BitSharp, Independent Researcher, Rzesz\'{o}w, Poland}
   28  \date{March 2026}
   32  \maketitle
   34  \begin{abstract}
   43  \end{abstract}
   46  \section{Introduction}
   70  \section{Related Work}
   73    \subsection{Post-Training Quantization for LLMs}
   83    \subsection{Quantization of Non-English Models}
   87    \subsection{The Bielik Model Family}
   92  \section{Methodology}
   95    \subsection{Overview}
   99      \begin{table}[htbp] .. 119 \end{table}   caption:101  \label{tab:variants}:102
  121    \subsection{Calibration Data and Hessian Generation}
  135    \subsection{Variant A: QuIP\# with E8P12 Lattice Codebook}
  149    \subsection{Variant B: SpinQuant + GPTQ}
  163    \subsection{Variant C: Butterfly Transforms + E8P}
  177    \subsection{Variant D: QTIP with Trellis Coded Quantization}
  187    \subsection{Variant E: VPTQ}
  200    \subsection{Variant F: AQLM}
  206      \begin{table}[htbp] .. 222 \end{table}   caption:208  \label{tab:aqlm_bitwidth}:209
  227  \section{Experimental Setup}
  230    \subsection{Hardware and Infrastructure}
  234      \begin{table}[htbp] .. 261 \end{table}   caption:236  \label{tab:gpu_allocation}:237
  267    \subsection{Evaluation Protocol}
  280      \label{eq:normalization}
  289  \section{Results}
  292    \subsection{Variant A: QuIP\# E8P12 --- Near-Parity with IQ2\_XXS}
  294      \begin{table}[htbp] .. 310 \end{table}   caption:296  \label{tab:variant_a}:297
  318      \begin{table}[htbp] .. 335 \end{table}   caption:320  \label{tab:task_deltas}:321
  339    \subsection{eq\_bench: Emotional Intelligence Advantage}
  343      \begin{table}[htbp] .. 357 \end{table}   caption:345  \label{tab:eqbench}:346
  361      \begin{table}[htbp] .. 373 \end{table}   caption:363  \label{tab:23task}:364
  375    \subsection{Variant B: SpinQuant + GPTQ --- Negative Result}
  383    \subsection{Variant C: ButterflyQuant + E8P --- Catastrophic Failure}
  389    \subsection{Variant D: QTIP --- Best Per-Bit Efficiency, Complete Evaluation}
  393      \begin{table}[htbp] .. 415 \end{table}   caption:395  \label{tab:qtip_mc}:396
  419      \begin{table}[htbp] .. 443 \end{table}   caption:421  \label{tab:qtip_gen}:422
  449      \begin{table}[htbp] .. 473 \end{table}   caption:451  \label{tab:qtip_vs_iq2}:452
  479    \subsection{Variant E: VPTQ --- Highest MC at Higher Bitrate}
  483      \begin{table}[htbp] .. 505 \end{table}   caption:485  \label{tab:vptq_mc}:486
  509    \subsection{Variant F: AQLM --- Competitive MC at Adaptive Bitwidth}
  513      \begin{table}[htbp] .. 535 \end{table}   caption:515  \label{tab:aqlm_mc}:516
  542  \section{Analysis}
  545    \subsection{MC-Generation Dissociation}     \label{sec:mc_gen_dissociation}:546
  556    \subsection{QuIP\# vs.\ IQ2\_XXS: Complementary Strengths}
  562    \subsection{Language-Specific Calibration}
  566    \subsection{Compression Characteristics}
  570    \subsection{FP16 Decompression Fidelity}
  574    \subsection{Cross-Method MC Comparison}
  578      \begin{table}[htbp] .. 605 \end{table}   caption:580  \label{tab:cross_mc}:581
  619    \subsection{Quality Ceiling at Extreme Compression}
  626  \section{Limitations}
  648  \section{Conclusion}
  667    \subsection{Future Work}
  672  \section*{Acknowledgments}
  678  \bibliographystyle{unsrt}
  680  \begin{thebibliography}{12}
  682/687/692/697/702/707/712/717/722/727/732/737  \bibitem{...}  (12 pozycji)
  742  \end{thebibliography}
  744  \end{document}
```

Podsumowanie liczbowe: **9 `\section`** (w tym 1 gwiazdkowa), **22 `\subsection`**, **0 `\subsubsection`**, **0 `\paragraph`**, **11 `\begin{table}`**, **0 `\begin{figure}`**, **0 `\includegraphics`**, **0 `\input` / `\include`**, **15 `\label`**, **12 `\bibitem`**, **1 abstrakt** (linie 34-43).

#### 2.2 `C:\Users\japre\Desktop\results_section.tex` (143 linie)

```
    1-6  komentarz naglowkowy: "Results section — Bielik-Minitron-7B-v3.0-Instruct quantization gradient
         / Quant levels: Q8_0 / Q4_K_M / Q2_K / Suite: 22-task agentic tool-use
         / Canonical run: commit 1b1af70, T=0, single seed, 2026-06-02."
    5  % Requires: \usepackage{booktabs}      <- komentarz, NIE komenda
    8  \section{Results}
   10    \paragraph{Setup.}
   23    \paragraph{Quantization gradient.}
   29      \begin{table}[t] .. 43 \end{table}   caption:40  \label{tab:gradient}:42
   45    \paragraph{Q2 is a collapse of a distinct kind.}
   55      \begin{table}[t] .. 73 \end{table}   caption:69  \label{tab:tags}:72
   75    \paragraph{Q4 $\geq$ Q8 reflects output conformance, not better reasoning.}
   87    \paragraph{Arithmetic over tool-returned data is a quantization-independent weak point.}
  106      \begin{table}[t] .. 128 \end{table}   caption:123  \label{tab:arith}:127
  130    \paragraph{Synthesis.}
  139    \paragraph{Limitations.}
```

**Brak `\documentclass`, `\begin{document}`, `\title`, `\author`, `\date`, `\begin{abstract}`, `\usepackage`, bibliografii.** To fragment do wklejenia, nie samodzielny dokument. Zawiera **3 `\begin{table}`**, **3 `\label`**, **7 `\paragraph`**, **1 `\section`**.

---

### CZESC 3 — Siedem punktow kontrolnych

**Zakres oceny:** dwa pliki `.tex` na dysku (`bielik_q2_sharp.tex`, `results_section.tex`). Papier docelowy nie istnieje (CZESC 1), wiec zaden z punktow nie moze byc w nim spelniony. Dla przejrzystosci dodaje kolumne "najblizszy artefakt na dysku" — pokazuje, czy dana tresc istnieje gdziekolwiek (PDF / SESSION_LOG.md), nawet jesli nie w .tex.

| # | Punkt | Werdykt (dla .tex) | Dowod |
|---|-------|--------------------|-------|
| 1 | Tytul „The Q2 Cliff…" + abstrakt o TRZECH modelach | **NIE** | `Q2 Cliff` = 0 wystapien w obu .tex (`scratchpad/kw.py`). `bielik_q2_sharp.tex:23` ma `\title{Bielik-Q2-Sharp: A Comparative Study of Extreme 2-bit\\Quantization Methods for a Polish 11B Language Model}` — inny papier, jeden model (11B), temat = metody kwantyzacji, nie agentyka. Abstrakt (linie 34-43) mowi o szesciu METODACH kwantyzacji jednego modelu, nie o trzech modelach. `results_section.tex` nie ma `\title` ani `\begin{abstract}` w ogole. |
| 2 | Relacja 7B↔11B (Minitron: pruning + destylacja, 11.04B → 7.35B, osobny alignment po destylacji) | **NIE** | `pruning` = 0, `11.04` = 0, `alignment` = 0 w obu .tex. `Minitron` wystepuje 2× w `results_section.tex` (linie 2 i 11) ale wylacznie jako czlon nazwy modelu: `\textsc{Bielik-Minitron-7B-v3.0-Instruct}` (linia 11). `7.35` wystepuje 2× w `bielik_q2_sharp.tex` (linie 464, 475) — to wartosci w tabelach GEN wariantu QTIP, nie liczba parametrow. Zadnego zdania o relacji miedzy modelami. |
| 3 | Envelope collapse podpiety pod fakty PLLuM (18 wystapien u PLLuM, convert 3.95×, 7B rozproszone) | **NIE** | `envelope` = 0, `koperta` = 0, `PLLuM` = 0, `3.95` = 0, `convert_temperature` = 0 w obu .tex. Nie ma tez blednej wersji („7B Q8, 18 wystapien") — nie ma **zadnej** wersji, wiec werdykt to NIE, nie BLEDNE. Poprawiona wersja faktu zyje tylko w `polagentbench/SESSION_LOG.md:626-629`: „Dokument przekazania mówił, że 18 wystąpień spłaszczonej koperty dotyczy **Bielika-7B Q8 na main** — to było **błędne**… jedynym runem `main67` z dokładnie 18 jest **PLLuM-8B Q8**." |
| 4 | Finding 3 przeformulowany (rusztowanie pomaga OBU modelom, podloga 7B = artefakt typowania, L0=0.00 osobno) | **NIE** | `Finding 3` = 0, `scaffold` = 0, `L0` = 0, `typing` (w sensie typowania pola) = 0 w obu .tex (2 trafienia `typing` w `bielik_q2_sharp.tex:131,232` to slowo w innym znaczeniu). Uwaga: **stara** formulacja istnieje poza .tex — `polagentbench_paper.pdf`, str. 7: „7 Finding 3 — The role of sca[ff]olding inverts" („inverts", czyli odwraca sie, a nie „pomaga obu"). Zrodlo: `scratchpad/pdftxt/polagentbench_paper_full.txt:456`. |
| 5 | Podsekcja atraktora „59" (91 par, zero wystapien w wejsciu i w srodowisku) | **NIE** | `attractor` = 0, `attraktor` = 0, `91 pair` = 0 w obu .tex. W `bielik_q2_sharp.tex` ciag „59" pada 6× (linie 461, 491, 511, 589, 710, 739) — wszystkie to liczby w tabelach MC/GEN i numer arXiv `2509.09679`, nic wspolnego z atraktorem. W `polagentbench_paper.pdf` rowniez 0 wystapien `attractor`. |
| 6 | Sekcja wariancji (dwumodalnosc = dyscyplina koperty, seed-per-step jako FAKT O KODZIE, bez twierdzenia przyczynowego) | **NIE** | `bimodal` = 0 w obu .tex. `variance` = 2 w `bielik_q2_sharp.tex` (linie 81, 128) — oba w kontekscie macierzy Hessego/kalibracji, nie wariancji wynikow. `seed` = 4 w `results_section.tex` (linie 4, 16, 84, 140) i wszystkie mowia dokladnie odwrotnie niz sekcja o wariancji: „single greedy seed", „single seed" — czyli deklaruja BRAK zmiennosci, a nie ja analizuja. `seed-per-step` = 0 wystapien. |
| 7 | Sensitivity analysis typowania (strict vs corrected, OBIE raty raportowane obok siebie) | **NIE** | `sensitivity` = 1 w `bielik_q2_sharp.tex:656`, ale w zdaniu „IQ2\_XXS preserves classification **sensitivity** (cbd: +11.11)" — to czulosc klasyfikacji, nie analiza wrazliwosci. `corrected` = 2 (linie 282, 550): linia 282 to „All results here use **corrected** official baselines" (poprawione baseline'y leaderboarda), linia 550 to „each generated token carries un**corrected** quantization error". Zadne z nich nie jest para strict/corrected dla typowania pola `answer`. W `results_section.tex` `strict` = 2 (linie 17, 95) ale w znaczeniu „strict tool-call ordering" i „the exact-literal criterion" — jedna rata, bez drugiej obok. Decyzja o raportowaniu obu rat istnieje wylacznie w `SESSION_LOG.md:634-639`. |

**Podsumowanie CZESCI 3: 0 punktow TAK, 7 punktow NIE, 0 punktow BLEDNE.** Zaden z siedmiu elementow nie ma reprezentacji w zadnym pliku `.tex` na maszynie.

Uwaga metodologiczna do punktu 3: instrukcja przewidywala werdykt BLEDNE, gdyby tekst „nadal mowil 7B Q8, 18 wystapien". Sprawdzilem to jawnie — `18` w kontekscie koperty nie wystepuje ani w `.tex`, ani w `polagentbench_paper.pdf` (slowo `envelope` ma tam 0 wystapien). Blednej wersji nie ma, bo nie ma zadnej.

---

### CZESC 4 — TODO / placeholdery / puste pola

Skrypt zrodlowy: `scratchpad/placeholders.py` (37 wzorcow markerow + rozwiazywanie `\ref`/`\cite`/`\label`/`\bibitem`). Wejscie: oba pliki `.tex`.

#### 4.1 `bielik_q2_sharp.tex`

| Kategoria | Wynik |
|-----------|-------|
| `TODO`, `XXX`, `FIXME`, `TBD`, `???`, `\todo`, `PLACEHOLDER`, `FILL`, `INSERT`, `\marginpar`, `\hl{`, `textcolor{red}` | **0 wystapien kazdego** |
| `[Author…]`, `[Affiliation]`, `[email]`, `[NAME]` | **0 wystapien** |
| `\ref{}` puste | **0** |
| `\cite{}` puste | **0** |
| `\ref` wskazujacy na nieistniejacy `\label` | **0** (15 labeli, wszystkie `\ref` rozwiazane) |
| `\cite` wskazujacy na nieistniejacy `\bibitem` | **0** (12 bibitemow, wszystkie `\cite` rozwiazane) |
| `\bibitem` niecytowany w tekscie | **0** (wszystkie 12 uzyte) |

**Ten plik jest czysty pod wzgledem markerow roboczych.** Realne braki, ktore zostaly (nie sa markerami, ale sa dziurami):

| Brak | Lokalizacja | Opis |
|------|-------------|------|
| Brak adresu e-mail autora | `bielik_q2_sharp.tex:25-26` | `\author{Jakub Prejzner\textsuperscript{1}\\ \textsuperscript{1}BitSharp, Independent Researcher, Rzesz\'{o}w, Poland}` — afiliacja jest, e-maila **nie ma nigdzie w pliku** (jedyne `@` w calym pliku to specyfikatory `\begin{tabular}{@{}…@{}}` w 13 tabelach: linie 103, 210, 238, 298, 322, 347, 365, 397, 423, 453, 487, 517, 582). |
| Brak ORCID | caly plik | 0 wystapien `orcid`. |
| Brak wlasnego numeru arXiv / DOI | caly plik | 0 wystapien `doi`, `10.48550`. Zadnego naglowka preprintu. |
| Brak licencji / oswiadczenia CC | caly plik | 0 wystapien `license`, `CC BY`. |
| Data bez dnia | `bielik_q2_sharp.tex:28` | `\date{March 2026}`. |

Link do artefaktow **jest** (nie jest to brak): `bielik_q2_sharp.tex:131`, przypis `\footnote{Available at \url{https://huggingface.co/Jakubrd4/bielik-quip-e8p12}}`, oraz `:735` `\url{https://huggingface.co/spaces/speakleash/open_pl_llm_leaderboard}` w bibliografii.

#### 4.2 `results_section.tex`

| Kategoria | Wynik |
|-----------|-------|
| `TODO`, `XXX`, `FIXME`, `TBD`, `???`, `\todo` | **0 wystapien** |
| `placeholder` | **2 wystapienia, oba to tresc merytoryczna, NIE markery**: `:97` „…a **placeholder** string (Q4), or a wrong intermediate mean…" (opis odpowiedzi modelu) oraz `:114` „`& Q4\_K\_M & --- & no-number (placeholder) \\`" (komorka tabeli, klasyfikacja przypadku). |
| `\ref` / `\cite` puste lub nierozwiazane | **0** (3 labele: `tab:gradient`, `tab:tags`, `tab:arith`; wszystkie `\ref` rozwiazane; 0 `\cite`) |
| Pola autora / afiliacji / e-maila | **NIE ISTNIEJA W OGOLE** — plik nie ma `\author`, `\title`, `\date`, `\documentclass`. To fragment. |
| Brakujace `\usepackage` | `:5` komentarz „`% Requires: \usepackage{booktabs}`" i `:123-126` w caption: „`Requires \texttt{\textbackslash usepackage\{multirow\}}`" — plik uzywa `\toprule`/`\midrule`/`\bottomrule` (linie 32,34,38,58,60,67,109,111,116,121) i `\multirow` (linie 112, 117), ale **nie deklaruje zadnego pakietu**. |

#### 4.3 Brakujacy numer arXiv poprzedniego papera — ROZSTRZYGNIETE

Poprzedni papier = `bielik_q2_sharp.tex` = „Bielik-Q2-Sharp".

- **W samym `bielik_q2_sharp.tex` jego numeru arXiv nie ma** (0 wystapien `doi`, `10.48550`; 9 wystapien `arXiv:` to wylacznie cudze prace w bibliografii, linie 685, 690, 695, 700, 705, 710, 725, 730, 740).
- **Numer JEST na dysku i wynosi `arXiv:2603.04162` (cs.CL).** Piec niezaleznych plikow-swiadkow (komenda: `grep -rl -F "2603.04162"`):
  - `C:\Users\japre\Downloads\AGENTS-bielik.md:12` — „`## Paper: Bielik-Q2-Sharp (arXiv:2603.04162, cs.CL)`"
  - `C:\Users\japre\Downloads\USER.md:8` — „`Opublikowany paper na arXiv: "Bielik-Q2-Sharp" (arXiv:2603.04162, cs.CL)`"
  - `C:\Users\japre\Downloads\CLAUDE (2).md:13` — „`Publikacja: arXiv 2603.04162 — ekstremalna kwantyzacja 2-bitowa polskiego modelu Bielik 11B.`"
  - `C:\Users\japre\Downloads\AGENTS-jobsearch.md:22, :43`
  - `C:\Users\japre\Downloads\PolAgentBench_preview.pdf`, str. 1 — „`Building on prior work: arXiv:2603.04162`"
- **Ten numer jest DZIURA w drafcie z 24 lipca.** `polagentbench_paper.pdf`, pozycja bibliografii [13] (ostatnia, str. 10) brzmi doslownie:

  > `[13] [AUTHOR'S PRIOR WORK — confirm exact arXiv identifier, title, and author list before submission.] Earlier study of low-bit quantization of Bielik.`

  Zrodlo: `scratchpad/pdftxt/polagentbench_paper_full.txt`, linia 797 (wyciag `pdftotext`; komenda weryfikujaca: `grep -n -F "AUTHOR'S PRIOR WORK"`).

  Czyli: numer poprzedniego papera **istnieje i jest znany** (2603.04162), ale w drafcie stoi na jego miejscu jawny placeholder. Zamkniecie tej dziury nie wymaga zadnego nowego pomiaru — wystarczy przepisanie z `USER.md`.

#### 4.4 Placeholdery w `polagentbench_paper.pdf` (nie .tex, ale jedyny pelny draft)

Wykryte przez `scratchpad/kw.py` na `scratchpad/pdftxt/polagentbench_paper_full.txt`:

| Linia wyciagu | Tresc | Strona PDF |
|---------------|-------|------------|
| 3 | `[Author Name]*1 1[Affiliation]` | 1 (blok autora) |
| 9 | `*Corresponding author: [email]. Preprint draft — bracketed items to be completed before submission.` | 1 (przypis) |
| 797 | `[13] [AUTHOR'S PRIOR WORK — confirm exact arXiv identifier, title, and author list before submission.] Earlier study of low-bit quantization of Bielik.` | 10 (bibliografia) |

Kontrola falszywych trafien: skaner zglosil poczatkowo takze `TBD` w linii 6 wyciagu — sprawdzilem recznie (`sed -n '6p' | grep -o -F "TBD"` → brak trafienia) i jest to **artefakt**: linia 6 to blok abstraktu, w ktorym `pdftotext` rozsypal kolejnosc znakow (dwukolumnowy uklad zlozony przez silnik PDF), a dopasowanie zaszlo bez uwzglednienia wielkosci liter na przypadkowym ciagu liter. **W drafcie nie ma markera `TBD`.**

**BRAK DANYCH** na temat dokladnych numerow linii tych placeholderow w zrodle: zrodlo `.tex` tego draftu nie istnieje na dysku (CZESC 1, punkt 3 i 4 tabeli komend). Podane numery to linie w wyciagu tekstowym, nie w zrodle.

---

### CZESC 5 — Identyfikatory arXiv 2604.19884, 2505.19433, 2605.07990

Komenda: `grep -rl -F "<ID>"` po `/c/Users/japre/{Desktop,Downloads,Documents,polagentbench}` oraz katalogu sekcji, z filtrem `--include` na `*.md *.txt *.tex *.bib *.json *.yaml *.ps1 *.py`, z pominieciem `.git`, `.venv`, `node_modules`. Osobno: `grep -n -F` w wyciagach `pdftotext` obu draftow PDF.

| ID | (a) w .bib lub `thebibliography` | (b) cytowany `\cite` | Gdzie w ogole wystepuje na dysku |
|----|----------------------------------|----------------------|----------------------------------|
| **2604.19884** | **NIE** | **NIE** | Tylko `scratchpad/fetch_arxiv.ps1` (skrypt pobierania metadanych napisany w tej sesji) i `scratchpad/kw.py` (moj wlasny skaner). Zero wystapien w `.tex`, `.pdf`, repo. |
| **2505.19433** | **NIE** | **NIE** | Jak wyzej — tylko `scratchpad/fetch_arxiv.ps1`, `scratchpad/kw.py`. |
| **2605.07990** | **NIE** | **NIE** | Jak wyzej — tylko `scratchpad/fetch_arxiv.ps1`, `scratchpad/kw.py`. |

Uzasadnienie „(a) NIE" jest mocniejsze niz brak trafienia grepa: **na calej maszynie nie ma ani jednego pliku `.bib`** (CZESC 1, komenda 2 i 3: 0 wynikow na C: i D:, poza `xampl.bib` z dystrybucji TinyTeX). Jedyny blok `thebibliography` w calym zbiorze zrodel to `bielik_q2_sharp.tex:680-742` i zawiera **12 pozycji**, o nastepujacych identyfikatorach arXiv (linie 685, 690, 695, 700, 705, 710, 725, 730, 740):

`2402.04396` (QuIP#), `2406.11235` (QTIP), `2405.16406` (SpinQuant), `2409.17066` (VPTQ), `2404.00456` (QuaRot), `2509.09679` (ButterflyQuant), `2401.06118` (AQLM), `2505.02410` (Bielik v2 technical report), `2309.09400` (CulturaX). Pozostale trzy pozycje (`frantar2023gptq` ICLR 2023, `lin2024awq` MLSys 2024, `speakleash2024leaderboard` URL) nie maja numeru arXiv.

Dla porzadku — bibliografia drugiego draftu (`polagentbench_paper.pdf`, 13 pozycji, str. 10) zawiera arXiv: `2505.08620`, `2601.14277`, `2509.26553`, `2511.22138`, `2410.18565`, `2505.02410`, `2505.02550` oraz placeholder [13]. **Rowniez zadnego z trzech szukanych ID.**

Wniosek: wszystkie trzy identyfikatory sa **kandydatami do zacytowania, nie cytowaniami** — pojawiaja sie wylacznie na liscie `$ids` w `scratchpad/fetch_arxiv.ps1` obok 10 innych, ktore w bibliografiach juz sa. Metadanych dla nich **nie pobrano**: katalog `scratchpad/arxiv_meta/` jest **pusty**, `scratchpad/arxiv.xml` ma **0 bajtow**, a `scratchpad/t1.xml` zawiera 14 bajtow o tresci `Rate exceeded.` — API arXiv odrzucilo zapytania. **BRAK DANYCH** o tytulach i autorach tych trzech prac; nie da sie ich ustalic z dysku.

---

### CZESC 6 (KROK 4) — Kompilacja

#### 6.1 Wykrywanie dystrybucji TeX

| Metoda | Wynik |
|--------|-------|
| `which pdflatex / xelatex / lualatex / latexmk / tectonic / tex / bibtex / biber` | **BRAK w PATH** — wszystkie 8 |
| `powershell Get-Command pdflatex, xelatex, lualatex, latexmk, tectonic, miktex-pdflatex` | **BRAK** — wszystkie 6 |
| `/c/Program Files/MiKTeX`, `/c/Program Files (x86)/MiKTeX`, `/c/texlive`, `/c/Program Files/texlive`, `%LOCALAPPDATA%\Programs\MiKTeX`, `%LOCALAPPDATA%\MiKTeX`, `%APPDATA%\MiKTeX` | **BRAK** — wszystkie 7 katalogow nie istnieja |
| `find "/c/Program Files" "/c/Program Files (x86)" /c/Users/japre/AppData/Local/Programs -maxdepth 5 -iname "pdflatex.exe"` | **0 wynikow** |
| **`ls /c/Users/japre/AppData/Roaming/TinyTeX/bin/windows`** | **ZNALEZIONE — 81 plikow .exe**, w tym `pdflatex.exe`, `xelatex.exe`, `lualatex.exe`, `latexmk.exe`, `bibtex.exe`, `kpsewhich.exe`, `latex.exe`, `tex.exe`, `tlmgr.bat` |

**Dystrybucja JEST.** `pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026)`, `kpathsea version 6.4.2`, `BibTeX 0.99e (TeX Live 2026)`. `TEXMFDIST = C:/Users/japre/AppData/Roaming/TinyTeX/texmf-dist`.

Dostepnosc wszystkich potrzebnych pakietow sprawdzona przez `kpsewhich` — **13 z 13 obecnych**: `article.cls`, `inputenc.sty`, `fontenc.sty`, `amsmath.sty`, `amssymb.sty`, `graphicx.sty`, `booktabs.sty`, `hyperref.sty`, `url.sty`, `natbib.sty`, `geometry.sty`, `xcolor.sty`, `multirow.sty`.

#### 6.2 Kompilacja `bielik_q2_sharp.tex`

Katalog: `scratchpad/texbuild/` (czysty, utworzony `rm -rf` + `mkdir`; jedyna zawartosc przed startem to kopia `bielik_q2_sharp.tex`). **Bez `-shell-escape`.**

```
cd scratchpad/texbuild
<TinyTeX>/pdflatex.exe -interaction=nonstopmode -file-line-error bielik_q2_sharp.tex   # x3
```

| Metryka | Wartosc |
|---------|---------|
| Wersja TeX | pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026), kpathsea 6.4.2 |
| Przebieg 1 — kod wyjscia | 1 (powod: 6 nierozwiazanych `\ref` przy pierwszym przebiegu, PDF mimo to powstal) |
| Przebieg 2 — kod wyjscia | **0** |
| Przebieg 3 — kod wyjscia | **0** |
| **PDF powstal** | **TAK** — `bielik_q2_sharp.pdf`, **302 424 B** |
| **Liczba stron** | **17** (`Output written on bielik_q2_sharp.pdf (17 pages, 302424 bytes)`) |
| **Bledy (`^!` w logu)** | **0** |
| **`.bbl` powstal** | **NIE — i nie jest potrzebny.** Plik uzywa inline `\begin{thebibliography}{12}` (linia 680), nie `\bibliography{...}`. `bibtex` nie byl uruchamiany. `ls *.bbl` → „No such file or directory". |
| **Undefined references** | **0** po przebiegu 2. Po przebiegu 1: **6** (`tab:variants` s.3/l.97; `sec:mc_gen_dissociation` s.5/l.161 i s.9/l.381; `tab:qtip_vs_iq2` s.9/l.447; `tab:cross_mc` s.13/l.576 i s.14/l.621) + 2 ostrzezenia zbiorcze („There were undefined references", „Label(s) may have changed. Rerun…"). To normalne zachowanie pierwszego przebiegu. |
| **Undefined citations** | **0** we wszystkich przebiegach |
| **LaTeX Warning ogolem** | przebieg 1: **8**; przebieg 3: **0** |
| **Package Warning** | **0** |
| **Overfull `\hbox`** | **9** |
| **Underfull `\hbox`** | **1** |
| **Overfull / Underfull `\vbox`** | **0 / 0** |

Pelna lista przepelnien (log: `scratchpad/texbuild/bielik_q2_sharp.log`; numery linii odnosza sie do zrodla `.tex`):

| # | Typ | Nadmiar | Linie zrodla | Fragment |
|---|-----|---------|--------------|----------|
| 1 | Overfull hbox | 9,53 pt | 89–90 | „…SpeakLeash collaboration with ACK Cyfronet AGH (grant PLG/2024/016951)." |
| 2 | Overfull hbox | 2,05 pt | 147–148 | „Architecture adaptation. Bielik-11B-v2.3-Instruct uses Mistral architecture…" |
| 3 | Overfull hbox | **45,07 pt** | 147–148 | „…natively supports only `LlamaForCausalLM`. We patched `model_from_hf_path()`…" ← najwieksze |
| 4 | Overfull hbox | 4,58 pt | 173–174 | „Four bugs were fixed: RedPajama dataset removal…, `rope_theta`/`rope_scaling`" |
| 5 | Overfull hbox | 16,00 pt | 181–182 | „`LlamaConfig` adaptation was required (`attention_bias`, `mlp_bias`…)" |
| 6 | Overfull hbox | 10,99 pt | 183–184 | „Preliminary generation tests showed preserved factual knowledge (…Kraków's…" |
| 7 | Overfull hbox | 7,16 pt | 447–448 | „GEN comparison with IQ2_XXS. Table 10 compares QTIP (finetuned)…" |
| 8 | Overfull hbox | 19,97 pt | 558–559 | „QuIP# advantages: Emotional reasoning (eq_bench: +3.61), multi-step…" |
| 9 | Overfull hbox | 0,74 pt | 616–617 | „NER is universally hardest. klej_ner ranges from 45.72% (QTIP) to 52.38%…" |
| 10 | Underfull hbox | badness 1533 | 733–736 | pozycja bibliografii `speakleash2024leaderboard` z dlugim `\url{}` |

Osiem z dziewieciu przepelnien to `\texttt{}` z dlugimi identyfikatorami kodu, ktorych LaTeX nie umie przelamac. Zadne nie jest bledem — PDF sie sklada.

Jednorazowy koszt pierwszego przebiegu: TinyTeX generowal brakujace bitmapy fontow EC przez `mf-nowin.exe` + `gftopk.exe` (widoczne w `pass1.log`, 73 844 B). Przebiegi 2 i 3 korzystaly juz z cache `texmf-var/fonts/pk/ljfour/jknappen/ec/` i byly szybkie.

#### 6.3 Kompilacja `results_section.tex` — nie kompiluje sie

Katalog `scratchpad/texbuild2/`, ta sama komenda.

```
EXIT = 1
results_section.log:4760  ! Emergency stop.
results_section.log:4761  <*> results_section.tex
results_section.log:4763  *** (job aborted, no legal \end found)
results_section.log:4774  ! ==> Fatal error occurred, no output PDF file produced!
```

**PDF nie powstal.** Przyczyna jest strukturalna, nie skladniowa: plik nie ma `\documentclass` ani `\begin{document}` (CZESC 2.2). Do skompilowania wymagalby opakowania oraz jawnego dodania `\usepackage{booktabs}` (uzywa `\toprule`/`\midrule`/`\bottomrule` w 12 miejscach) i `\usepackage{multirow}` (linie 112, 117) — oba zadania sa w pliku zapisane jako komentarz/tekst caption, nie jako komendy.

#### 6.4 Analiza statyczna zaleznosci (dla kompletnosci — tarball arXiv)

`\usepackage` w `bielik_q2_sharp.tex` — **10 deklaracji, linie 3-12**:

| Linia | Pakiet | Status |
|-------|--------|--------|
| 3 | `inputenc` (opcja `utf8`) | standard TeX Live, obecny |
| 4 | `fontenc` (opcja `T1`) | standard, obecny |
| 5 | `amsmath, amssymb, amsfonts` | standard, obecne |
| 6 | `graphicx` | standard, obecny (ale **nieuzywany** — 0 `\includegraphics`) |
| 7 | `booktabs` | standard, obecny |
| 8 | `hyperref` | standard, obecny |
| 9 | `url` | standard, obecny |
| 10 | `natbib` | standard, obecny (ale bibliografia jest inline `thebibliography`, wiec natbib nie robi nic poza przedefiniowaniem `\cite`) |
| 11 | `geometry` | standard, obecny |
| 12 | `xcolor` | standard, obecny |

`\includegraphics` / `\input{}` / `\include{}` / `\bibliography{}`: **po 0 wystapien**. Sprawdzenie: `grep -n -F -e '\includegraphics' -e '\input{' -e '\include{' -e '\bibliography{'` → brak trafien. Nie ma zatem **zadnego** pliku zewnetrznego — ani wewnatrz katalogu papera, ani poza nim. Dokument jest w pelni samodzielny.

**Lista plikow do tarballa zrodel arXiv dla `bielik_q2_sharp.tex`:**

| Plik | Konieczny? |
|------|-----------|
| `bielik_q2_sharp.tex` | TAK — jedyny plik zrodlowy |
| `.bbl` | NIE — bibliografia inline; arXiv nie uruchamia bibtexa i nie ma czego dolaczac |
| grafiki | NIE — brak |
| `.sty` / `.cls` lokalne | NIE — wszystkie 10 pakietow + `article.cls` sa w standardowym TeX Live |

Tarball zrodel to **jeden plik**, 53 035 B.

Dla papieru docelowego: **BRAK DANYCH** — nie ma zrodla, wiec nie da sie ustalic ani jego listy `\usepackage`, ani zaleznosci graficznych, ani zawartosci tarballa. Ta lista bedzie mogla powstac dopiero po napisaniu `.tex`.

---

### Pliki wytworzone przez ten audyt (wszystkie w scratchpadzie, nic poza nim)

| Sciezka | Zawartosc |
|---------|-----------|
| `scratchpad/sections/06_tex_audit.md` | ten raport |
| `scratchpad/texstruct.py` | skaner struktury LaTeX (CZESC 2) |
| `scratchpad/kw.py` | skaner 57 fraz kluczowych (CZESC 3, 4, 5) |
| `scratchpad/placeholders.py` | skaner markerow + walidator `\ref`/`\cite`/`\label`/`\bibitem` (CZESC 4) |
| `scratchpad/struct_bq2s.txt`, `scratchpad/ph_bq2s.txt` | surowe wyjscia powyzszych |
| `scratchpad/gitlog_added.txt` | `git log --all --diff-filter=A --name-only` (245 linii) |
| `scratchpad/pdftxt/*.txt` | wyciagi `pdftotext` z `polagentbench_paper.pdf`, `PolAgentBench_preview.pdf`, `Bielik-Q2-Sharp_arXiv_EN_v2.pdf` |
| `scratchpad/texbuild/` | udana kompilacja: `bielik_q2_sharp.{tex,pdf,log,aux,out}`, `pass1.log`, `pass2.log`, `pass3.log` |
| `scratchpad/texbuild2/` | nieudana kompilacja `results_section.tex`: `results_section.log`, `rs.log` |

Repo `C:\Users\japre\polagentbench` i pliki na Desktopie/Downloads **nie byly modyfikowane** — czytane tylko do odczytu, kopiowane do scratchpada przed kompilacja.

---
