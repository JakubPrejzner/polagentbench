# night_scripts — zapis historyczny

Te siedem plików to harness, którym wykonano nocną sesję pomiarową z 2026-07-29
(commit `e584b38`): rozszerzoną drabinę dla obu Bielików, pełną krzywą PLLuM-8B,
uzupełnienie siatki 7B o Q6_K i Q5_K_M oraz sondę wariancji przy `T=0.7`.

**To jest zapis historyczny, nie narzędzie do ponownego użycia.** Skrypty mają
zaszytą na sztywno ścieżkę `/workspace/polagentbench` (katalog roboczy wynajętej
maszyny GPU) i zakładają układ katalogów tamtego środowiska. Nie uruchomią się
bez zmian gdzie indziej. Publikujemy je, bo są jedynym zapisem tego, jak dokładnie
powstały dane w `../trajectories/` — łącznie z kolejnością faz, decyzjami bramek
i wartościami przekazanymi do CLI.

Przebieg tamtej nocy, z decyzjami i alertami, jest w `../NIGHT_LOG.txt`.

| plik | rola |
|---|---|
| `lib.sh` | wspólne funkcje: pobranie modelu, jeden przebieg, logowanie |
| `run_phase.sh` | jedna faza: model × lista kwantów × suite, warianty repair off/on |
| `phase3.sh` | drabina rozszerzona dla Bielika-7B |
| `phase5.sh` | sonda wariancji, `T=0.7`, ziarna 1/2/3 |
| `bonus_pllum.sh` | krzywa PLLuM-8B, sześć kwantów, main67 i ladder46 |
| `chain.sh` | spinacz faz |
| `measure_ctx.py` | bramka B: pomiar szczytowego `prompt_tokens` przed ustaleniem `n_ctx` |

Pomiar z `measure_ctx.py` jest tym, na którym oparto zdanie z papera o oknie
kontekstu: szczyt wyniósł 2308 tokenów przy progu 7000, więc `n_ctx` zostało
na domyślnych 8192 dla wszystkich modeli, bez asymetrii między PLLuM a Bielikami.
