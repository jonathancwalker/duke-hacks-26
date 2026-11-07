| library | text | method | top1 unique | top1 entropy | top1 ent/picks | max share | top3 unique | hubness k5 | para overlap@3 | para lift@3 | para/rand | opp/rand | biggest hub |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 36 | - | random (reference) | 23/36 | 0.82 | 0.82 | 0.10 | 33 | 0.74 | 0.12 | 0.03 | 1.02 | 0.95 | Seurat (4/40) |
| 36 | baseline | cosine | 9/36 | 0.44 | 0.44 | 0.55 | 21 | 1.84 | 0.53 | 0.24 | 0.67 | 0.91 | Friedrich (22/40) |
| 36 | raw | cosine | 15/36 | 0.56 | 0.56 | 0.45 | 22 | 1.77 | 0.47 | 0.21 | 0.78 | 1.02 | Friedrich (18/40) |
| 36 | evokes | cosine | 11/36 | 0.54 | 0.54 | 0.35 | 21 | 2.11 | 0.52 | 0.15 | 0.71 | 0.91 | Whistler (14/40) |
| 36 | mood | cosine | 14/36 | 0.59 | 0.59 | 0.35 | 22 | 1.59 | 0.43 | 0.13 | 0.73 | 0.97 | Friedrich (14/40) |
| 36 | emotion | cosine | 10/36 | 0.39 | 0.39 | 0.62 | 18 | 2.16 | 0.53 | 0.21 | 0.73 | 0.97 | Munch (25/40) |
| 36 | atmosphere | cosine | 10/36 | 0.52 | 0.52 | 0.38 | 18 | 2.04 | 0.57 | 0.14 | 0.77 | 1.00 | Monet (15/40) |
| 36 | ensemble | cosine | 10/36 | 0.52 | 0.52 | 0.30 | 18 | 1.88 | 0.55 | 0.23 | 0.73 | 0.96 | Friedrich (12/40) |
| 36 | baseline | center_img | 9/36 | 0.41 | 0.41 | 0.60 | 19 | 1.89 | 0.52 | 0.20 | 0.76 | 0.94 | Friedrich (24/40) |
| 36 | baseline | center_both | 17/36 | 0.73 | 0.73 | 0.15 | 27 | 1.25 | 0.35 | 0.17 | 0.74 | 0.91 | Renoir (6/40) |
| 36 | baseline | center_both_query* | 24/36 | 0.85 | 0.85 | 0.10 | 35 | 0.22 | 0.32 | 0.24 | 0.76 | 1.01 | Tanner (4/40) |
| 36 | baseline | gap_shift | 10/36 | 0.61 | 0.61 | 0.23 | 16 | 1.83 | 0.53 | 0.19 | 0.76 | 0.93 | Van Gogh (9/40) |
| 36 | baseline | whiten8 | 18/36 | 0.73 | 0.73 | 0.23 | 27 | 1.15 | 0.38 | 0.22 | 0.73 | 0.94 | Van Gogh (9/40) |
| 36 | baseline | whiten16 | 18/36 | 0.73 | 0.73 | 0.20 | 28 | 1.51 | 0.38 | 0.20 | 0.75 | 0.92 | Van Gogh (8/40) |
| 36 | baseline | whiten32 | 13/36 | 0.66 | 0.66 | 0.17 | 27 | 1.17 | 0.35 | 0.18 | 0.77 | 0.98 | Van Gogh (7/40) |
| 36 | baseline | csls | 16/36 | 0.67 | 0.67 | 0.28 | 24 | 1.77 | 0.43 | 0.23 | 0.70 | 0.94 | Friedrich (11/40) |
| 36 | baseline | zscore | 15/36 | 0.71 | 0.71 | 0.12 | 28 | 1.45 | 0.35 | 0.18 | 0.77 | 0.88 | Van Gogh (5/40) |
| 36 | baseline | center_both+csls | 15/36 | 0.71 | 0.71 | 0.12 | 27 | 1.46 | 0.38 | 0.20 | 0.77 | 0.92 | Van Gogh (5/40) |
| 36 | baseline | center_both+zscore | 14/36 | 0.69 | 0.69 | 0.15 | 28 | 1.51 | 0.35 | 0.16 | 0.80 | 0.90 | Van Gogh (6/40) |
| 36 | baseline | whiten16+zscore | 15/36 | 0.68 | 0.68 | 0.23 | 25 | 1.80 | 0.43 | 0.21 | 0.79 | 0.93 | Caillebotte (9/40) |
| 36 | ensemble | center_img | 11/36 | 0.53 | 0.53 | 0.30 | 18 | 1.86 | 0.55 | 0.23 | 0.73 | 0.96 | Friedrich (12/40) |
| 36 | ensemble | center_both | 18/36 | 0.76 | 0.76 | 0.15 | 32 | 1.03 | 0.35 | 0.22 | 0.81 | 0.93 | Tanner (6/40) |
| 36 | ensemble | center_both_query* | 23/36 | 0.85 | 0.85 | 0.10 | 36 | 0.56 | 0.30 | 0.23 | 0.77 | 0.95 | Tanner (4/40) |
| 36 | ensemble | gap_shift | 9/36 | 0.58 | 0.58 | 0.17 | 18 | 1.79 | 0.55 | 0.21 | 0.72 | 0.95 | Monet (7/40) |
| 36 | ensemble | whiten8 | 17/36 | 0.75 | 0.75 | 0.12 | 28 | 0.93 | 0.33 | 0.17 | 0.80 | 0.98 | Delacroix (5/40) |
| 36 | ensemble | whiten16 | 19/36 | 0.78 | 0.78 | 0.12 | 32 | 1.31 | 0.27 | 0.14 | 0.78 | 0.96 | Renoir (5/40) |
| 36 | ensemble | whiten32 | 19/36 | 0.77 | 0.77 | 0.12 | 32 | 1.24 | 0.27 | 0.13 | 0.77 | 0.98 | Bruegel (5/40) |
| 36 | ensemble | csls | 18/36 | 0.74 | 0.74 | 0.17 | 24 | 1.34 | 0.45 | 0.28 | 0.70 | 0.92 | Tanner (7/40) |
| 36 | ensemble | zscore | 21/36 | 0.80 | 0.80 | 0.15 | 31 | 0.86 | 0.33 | 0.21 | 0.76 | 0.89 | Tanner (6/40) |
| 36 | ensemble | center_both+csls | 20/36 | 0.79 | 0.79 | 0.12 | 32 | 0.89 | 0.33 | 0.20 | 0.81 | 0.95 | Tanner (5/40) |
| 36 | ensemble | center_both+zscore | 20/36 | 0.78 | 0.78 | 0.12 | 32 | 0.91 | 0.32 | 0.17 | 0.80 | 0.96 | Rembrandt (5/40) |
| 36 | ensemble | whiten16+zscore | 19/36 | 0.76 | 0.76 | 0.17 | 30 | 1.37 | 0.42 | 0.27 | 0.75 | 0.96 | Caillebotte (7/40) |
| 36 | baseline/Rsent | center_img | 9/36 | 0.41 | 0.41 | 0.60 | 19 | 1.89 | 0.52 | 0.20 | 0.76 | 0.94 | Friedrich (24/40) |
| 36 | baseline/Rsent | center_both | 24/36 | 0.85 | 0.85 | 0.10 | 35 | 0.39 | 0.33 | 0.24 | 0.76 | 0.97 | Tanner (4/40) |
| 36 | baseline/Rsent | center_both_query* | 24/36 | 0.85 | 0.85 | 0.10 | 35 | 0.22 | 0.32 | 0.24 | 0.76 | 1.01 | Tanner (4/40) |
| 36 | baseline/Rsent | gap_shift | 10/36 | 0.57 | 0.57 | 0.23 | 17 | 1.72 | 0.50 | 0.19 | 0.72 | 1.03 | Munch (9/40) |
| 36 | baseline/Rsent | whiten8 | 20/36 | 0.76 | 0.76 | 0.17 | 33 | 0.72 | 0.32 | 0.20 | 0.72 | 1.00 | Tanner (7/40) |
| 36 | baseline/Rsent | whiten16 | 19/36 | 0.77 | 0.77 | 0.15 | 33 | 0.63 | 0.27 | 0.15 | 0.77 | 0.94 | Goya (6/40) |
| 36 | baseline/Rsent | whiten32 | 17/36 | 0.76 | 0.76 | 0.12 | 33 | 0.52 | 0.40 | 0.28 | 0.77 | 0.98 | Renoir (5/40) |
| 36 | baseline/Rsent | csls | 19/36 | 0.77 | 0.77 | 0.12 | 26 | 1.46 | 0.37 | 0.20 | 0.70 | 1.00 | Friedrich (5/40) |
| 36 | baseline/Rsent | zscore | 18/36 | 0.77 | 0.77 | 0.10 | 33 | 0.69 | 0.42 | 0.30 | 0.75 | 1.00 | Bruegel (4/40) |
| 36 | baseline/Rsent | center_both+csls | 24/36 | 0.85 | 0.85 | 0.10 | 35 | 0.60 | 0.33 | 0.23 | 0.72 | 1.01 | Tanner (4/40) |
| 36 | baseline/Rsent | center_both+zscore | 21/36 | 0.81 | 0.81 | 0.10 | 35 | 0.84 | 0.38 | 0.28 | 0.71 | 1.00 | Monet (4/40) |
| 36 | baseline/Rsent | whiten16+zscore | 21/36 | 0.81 | 0.81 | 0.10 | 31 | 0.67 | 0.33 | 0.23 | 0.75 | 0.91 | Van Gogh (4/40) |
| 36 | ensemble/Rsent | center_img | 11/36 | 0.53 | 0.53 | 0.30 | 18 | 1.86 | 0.55 | 0.23 | 0.73 | 0.96 | Friedrich (12/40) |
| 36 | ensemble/Rsent | center_both | 20/36 | 0.80 | 0.80 | 0.15 | 36 | 1.00 | 0.33 | 0.23 | 0.78 | 0.98 | Tanner (6/40) |
| 36 | ensemble/Rsent | center_both_query* | 23/36 | 0.85 | 0.85 | 0.10 | 36 | 0.56 | 0.30 | 0.23 | 0.77 | 0.95 | Tanner (4/40) |
| 36 | ensemble/Rsent | gap_shift | 10/36 | 0.57 | 0.57 | 0.25 | 16 | 1.69 | 0.50 | 0.14 | 0.67 | 0.93 | Monet (10/40) |
| 36 | ensemble/Rsent | whiten8 | 20/36 | 0.77 | 0.77 | 0.17 | 32 | 0.67 | 0.30 | 0.19 | 0.79 | 1.00 | Tanner (7/40) |
| 36 | ensemble/Rsent | whiten16 | 20/36 | 0.79 | 0.79 | 0.15 | 34 | 0.42 | 0.30 | 0.20 | 0.78 | 0.92 | Goya (6/40) |
| 36 | ensemble/Rsent | whiten32 | 21/36 | 0.80 | 0.80 | 0.12 | 33 | 0.93 | 0.38 | 0.27 | 0.74 | 0.98 | Renoir (5/40) |
| 36 | ensemble/Rsent | csls | 19/36 | 0.77 | 0.77 | 0.15 | 26 | 1.56 | 0.38 | 0.21 | 0.73 | 0.97 | Tanner (6/40) |
| 36 | ensemble/Rsent | zscore | 20/36 | 0.79 | 0.79 | 0.15 | 35 | 1.10 | 0.28 | 0.17 | 0.78 | 0.97 | Tanner (6/40) |
| 36 | ensemble/Rsent | center_both+csls | 21/36 | 0.81 | 0.81 | 0.12 | 36 | 1.00 | 0.35 | 0.24 | 0.77 | 1.01 | Tanner (5/40) |
| 36 | ensemble/Rsent | center_both+zscore | 19/36 | 0.77 | 0.77 | 0.15 | 36 | 1.00 | 0.28 | 0.18 | 0.75 | 0.98 | Tanner (6/40) |
| 36 | ensemble/Rsent | whiten16+zscore | 20/36 | 0.80 | 0.80 | 0.10 | 33 | 0.69 | 0.28 | 0.17 | 0.80 | 0.93 | Goya (4/40) |
| 36 | baseline/Rsent-A | center_both | 21/36 | 0.80 | 0.80 | 0.12 | 33 | 1.09 | 0.37 | 0.26 | 0.72 | 1.03 | Tanner (5/40) |
| 36 | baseline/Rsent-A | zscore | 20/36 | 0.80 | 0.80 | 0.12 | 32 | 0.83 | 0.38 | 0.28 | 0.72 | 1.01 | Fan Kuan (5/40) |
| 36 | baseline/Rsent-A | center_both+zscore | 19/36 | 0.80 | 0.80 | 0.10 | 31 | 0.84 | 0.33 | 0.21 | 0.72 | 1.01 | Bruegel (4/40) |
| 36 | baseline/Rsent-B | center_both | 24/36 | 0.85 | 0.85 | 0.10 | 34 | 0.23 | 0.32 | 0.22 | 0.74 | 0.97 | Tanner (4/40) |
| 36 | baseline/Rsent-B | zscore | 19/36 | 0.78 | 0.78 | 0.15 | 32 | 0.48 | 0.35 | 0.24 | 0.74 | 0.95 | Renoir (6/40) |
| 36 | baseline/Rsent-B | center_both+zscore | 17/36 | 0.74 | 0.74 | 0.15 | 33 | 0.85 | 0.32 | 0.21 | 0.74 | 1.02 | Renoir (6/40) |
| 305 | - | random (reference) | 37/305 | 0.63 | 0.97 | 0.05 | 99 | 1.08 | 0.00 | -0.01 | 1.01 | 1.00 | Turner (2/40) |
| 305 | baseline | cosine | 17/305 | 0.42 | 0.65 | 0.28 | 40 | 6.26 | 0.37 | 0.20 | 0.72 | 1.04 | Friedrich (11/40) |
| 305 | baseline | center_both | 34/305 | 0.61 | 0.94 | 0.05 | 79 | 2.21 | 0.13 | 0.10 | 0.81 | 1.00 | Tanner (2/40) |
| 305 | baseline | whiten16 | 28/305 | 0.56 | 0.87 | 0.10 | 59 | 3.53 | 0.20 | 0.15 | 0.82 | 1.03 | Claude Monet (4/40) |
| 305 | baseline | whiten64 | 30/305 | 0.57 | 0.88 | 0.10 | 71 | 3.83 | 0.28 | 0.24 | 0.78 | 0.97 | Tanner (4/40) |
| 305 | baseline | csls | 28/305 | 0.56 | 0.87 | 0.12 | 60 | 3.58 | 0.23 | 0.18 | 0.82 | 0.99 | Friedrich (5/40) |
| 305 | baseline | zscore | 34/305 | 0.61 | 0.94 | 0.05 | 73 | 2.38 | 0.13 | 0.10 | 0.83 | 0.98 | Van Gogh (2/40) |
| 305 | baseline | center_both+csls | 37/305 | 0.63 | 0.97 | 0.05 | 80 | 2.02 | 0.15 | 0.12 | 0.84 | 0.98 | Paul Cezanne (2/40) |
| 305 | baseline | center_both+zscore | 26/305 | 0.54 | 0.83 | 0.15 | 74 | 3.45 | 0.18 | 0.14 | 0.83 | 0.94 | Nicholas Roerich (6/40) |
| 305 | baseline | whiten64+zscore | 26/305 | 0.53 | 0.82 | 0.20 | 66 | 4.54 | 0.27 | 0.21 | 0.79 | 0.98 | Camille Pissarro (8/40) |
| 305 | ensemble | cosine | 20/305 | 0.47 | 0.73 | 0.20 | 37 | 6.09 | 0.38 | 0.20 | 0.72 | 0.99 | Munch (8/40) |
| 305 | ensemble | center_both | 33/305 | 0.60 | 0.93 | 0.07 | 82 | 1.76 | 0.17 | 0.14 | 0.83 | 0.98 | Rembrandt (3/40) |
| 305 | ensemble | whiten16 | 34/305 | 0.61 | 0.94 | 0.07 | 79 | 3.20 | 0.13 | 0.10 | 0.90 | 0.96 | Boris Kustodiev (3/40) |
| 305 | ensemble | whiten64 | 30/305 | 0.58 | 0.90 | 0.07 | 73 | 1.83 | 0.17 | 0.14 | 0.85 | 1.00 | Pyotr Konchalovsky (3/40) |
| 305 | ensemble | csls | 29/305 | 0.57 | 0.89 | 0.07 | 65 | 3.24 | 0.18 | 0.13 | 0.79 | 0.96 | Tanner (3/40) |
| 305 | ensemble | zscore | 32/305 | 0.59 | 0.91 | 0.07 | 86 | 1.70 | 0.15 | 0.13 | 0.86 | 0.97 | Tanner (3/40) |
| 305 | ensemble | center_both+csls | 34/305 | 0.61 | 0.94 | 0.07 | 84 | 1.77 | 0.13 | 0.11 | 0.84 | 0.98 | Nicholas Roerich (3/40) |
| 305 | ensemble | center_both+zscore | 32/305 | 0.59 | 0.91 | 0.10 | 81 | 2.41 | 0.13 | 0.11 | 0.86 | 0.94 | Nicholas Roerich (4/40) |
| 305 | ensemble | whiten64+zscore | 30/305 | 0.58 | 0.89 | 0.10 | 81 | 2.31 | 0.17 | 0.15 | 0.81 | 0.97 | Nicholas Roerich (4/40) |
| 305 | baseline/Rsent | cosine | 17/305 | 0.42 | 0.65 | 0.28 | 40 | 6.26 | 0.37 | 0.20 | 0.72 | 1.04 | Friedrich (11/40) |
| 305 | baseline/Rsent | center_both | 35/305 | 0.61 | 0.95 | 0.05 | 81 | 1.56 | 0.18 | 0.16 | 0.84 | 0.99 | Rembrandt (2/40) |
| 305 | baseline/Rsent | whiten16 | 32/305 | 0.59 | 0.92 | 0.07 | 90 | 2.01 | 0.12 | 0.11 | 0.82 | 1.02 | Salvador Dali (3/40) |
| 305 | baseline/Rsent | whiten64 | 34/305 | 0.61 | 0.94 | 0.05 | 84 | 1.59 | 0.13 | 0.11 | 0.88 | 0.99 | Tanner (2/40) |
| 305 | baseline/Rsent | csls | 29/305 | 0.57 | 0.89 | 0.07 | 65 | 3.50 | 0.22 | 0.18 | 0.80 | 0.96 | Friedrich (3/40) |
| 305 | baseline/Rsent | zscore | 35/305 | 0.61 | 0.95 | 0.05 | 91 | 1.67 | 0.10 | 0.09 | 0.92 | 0.99 | Munch (2/40) |
| 305 | baseline/Rsent | center_both+csls | 33/305 | 0.60 | 0.93 | 0.05 | 82 | 1.65 | 0.17 | 0.14 | 0.84 | 0.99 | Rembrandt (2/40) |
| 305 | baseline/Rsent | center_both+zscore | 35/305 | 0.61 | 0.95 | 0.05 | 89 | 1.61 | 0.17 | 0.15 | 0.86 | 1.01 | Munch (2/40) |
| 305 | baseline/Rsent | whiten64+zscore | 37/305 | 0.63 | 0.97 | 0.05 | 85 | 1.86 | 0.17 | 0.15 | 0.87 | 1.01 | Munch (2/40) |
| 305 | ensemble/Rsent | cosine | 20/305 | 0.47 | 0.73 | 0.20 | 37 | 6.09 | 0.38 | 0.20 | 0.72 | 0.99 | Munch (8/40) |
| 305 | ensemble/Rsent | center_both | 33/305 | 0.60 | 0.93 | 0.07 | 81 | 1.70 | 0.18 | 0.16 | 0.82 | 0.99 | Ivan Shishkin (3/40) |
| 305 | ensemble/Rsent | whiten16 | 37/305 | 0.62 | 0.97 | 0.07 | 94 | 2.02 | 0.07 | 0.06 | 0.88 | 1.01 | Pyotr Konchalovsky (3/40) |
| 305 | ensemble/Rsent | whiten64 | 37/305 | 0.63 | 0.97 | 0.05 | 88 | 1.57 | 0.13 | 0.11 | 0.86 | 0.95 | Ivan Shishkin (2/40) |
| 305 | ensemble/Rsent | csls | 29/305 | 0.57 | 0.89 | 0.10 | 64 | 3.36 | 0.20 | 0.14 | 0.81 | 0.95 | Munch (4/40) |
| 305 | ensemble/Rsent | zscore | 38/305 | 0.63 | 0.98 | 0.05 | 89 | 1.41 | 0.20 | 0.18 | 0.85 | 1.00 | Ivan Shishkin (2/40) |
| 305 | ensemble/Rsent | center_both+csls | 33/305 | 0.60 | 0.93 | 0.07 | 84 | 1.49 | 0.18 | 0.16 | 0.82 | 1.00 | Ilya Repin (3/40) |
| 305 | ensemble/Rsent | center_both+zscore | 33/305 | 0.60 | 0.93 | 0.05 | 87 | 1.47 | 0.18 | 0.17 | 0.82 | 1.01 | Camille Pissarro (2/40) |
| 305 | ensemble/Rsent | whiten64+zscore | 32/305 | 0.59 | 0.92 | 0.07 | 88 | 1.73 | 0.10 | 0.08 | 0.88 | 0.97 | Munch (3/40) |
| 305 | baseline/Rsent-A | center_both | 34/305 | 0.61 | 0.94 | 0.05 | 80 | 1.75 | 0.17 | 0.14 | 0.84 | 0.99 | Rembrandt (2/40) |
| 305 | baseline/Rsent-A | zscore | 32/305 | 0.59 | 0.92 | 0.07 | 84 | 1.70 | 0.15 | 0.13 | 0.86 | 1.01 | John Singer Sargent (3/40) |
| 305 | baseline/Rsent-A | center_both+zscore | 30/305 | 0.58 | 0.89 | 0.10 | 77 | 2.13 | 0.20 | 0.16 | 0.86 | 1.01 | Camille Pissarro (4/40) |
| 305 | baseline/Rsent-B | center_both | 36/305 | 0.62 | 0.96 | 0.05 | 82 | 1.74 | 0.20 | 0.18 | 0.84 | 0.99 | Rembrandt (2/40) |
| 305 | baseline/Rsent-B | zscore | 36/305 | 0.62 | 0.96 | 0.05 | 90 | 1.65 | 0.08 | 0.06 | 0.89 | 0.98 | Claude Monet (2/40) |
| 305 | baseline/Rsent-B | center_both+zscore | 33/305 | 0.59 | 0.92 | 0.10 | 85 | 1.95 | 0.20 | 0.18 | 0.83 | 1.01 | Claude Monet (4/40) |
