# Klasifikacija slika odeće: kategorija, podkategorija i boja

Završni projekat iz predmeta **Mašinsko učenje**.

Na osnovu slike artikla model predviđa:
- **kategoriju** (npr. Tops, Bottoms, Bags, Outerwear)
- **podkategoriju** (npr. Hoodie, Jeans, Handbag, Jacket)
- **boju** / porodicu boje (Black, Blue, Red...)

Pored klasičnog CNN-a implementiranog od nule (pristup sa vežbi), upoređen je i
**transfer learning** (ResNet18 pretreniran na ImageNet-u).

## Tim

- Irina Marko (1134/2025)
- Nikola Lazarević (mi251043)

## Opis skupa podataka

Skup **nije** javni dataset. Slike i metapodaci dolaze iz internih Fashion Company
order form Excel fajlova (Guess, Marciano, Kids, Footwear, Handbags, Levi's, Hugo Boss).
Slika artikla je ugrađena u ćeliju tabele.

Labele nisu crtane rukom. Izvedene su automatski iz zvaničnih pravila firme:
- **Item Tree** → kategorija / podkategorija
- **Paleta boja** → porodica boje

**Rezultat labeliranja: 6742 slike, 0 neuparenih redova.**

Ulazni Excel fajlovi (`exceli/`, `pravila/`) nisu u repozitorijumu (interni podaci).
U repou su izvedeni podaci: `data/`, `dataset/labels.csv`, `dataset/images/`,
`dataset/splits/` — pa se treniranje može ponoviti od koraka 04.

Osnovna analiza skupa (struktura, balans klasa, raspodela po izvorima) je u
[`00_eda.ipynb`](00_eda.ipynb).

## Rezultati (test skup)

| Zadatak | Klasa | Scratch CNN (acc / macro-F1) | Transfer ResNet18 (acc / macro-F1) |
|---|---|---|---|
| category | 14 | 0.642 / 0.622 | **0.736 / 0.762** |
| subcategory | 30 | 0.480 / 0.429 | **0.656 / 0.604** |
| color | 12 | **0.671 / 0.514** | 0.594 / 0.504 |

Transfer learning pobeđuje na zadacima oblika (kategorija, podkategorija), a **gubi na
boji** — ImageNet obeležja su naučena da boju delom ignorišu.

Detalji, matrice konfuzije i stubići poređenja:
- [`results/comparison.txt`](results/comparison.txt)
- [`results/plots/`](results/plots/)
- demo: [`06_demo.ipynb`](06_demo.ipynb)
- šira dokumentacija: [`DOKUMENTACIJA.md`](DOKUMENTACIJA.md)

Istrenirani modeli su u `models/` (`*_best.pt`). Fajlovi su ~18–43 MB po modelu
(ispod GitHub limita od 100 MB), pa su u repou.

## Podešavanje okruženja

Preporuka: Python 3.10+ (testirano na 3.14).

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
# source .venv/bin/activate

pip install -r requirements.txt
```

Za GPU verziju PyTorch-a: https://pytorch.org/get-started/locally/

## Redosled pregleda projekta

1. [`00_eda.ipynb`](00_eda.ipynb) — analiza skupa
2. `scripts/01_parse_rules.py` … `05_train_models.py` — pipeline
3. [`06_demo.ipynb`](06_demo.ipynb) — učitavanje modela, predikcija, rezultati
4. [`DOKUMENTACIJA.md`](DOKUMENTACIJA.md) — detaljan opis

## Pokretanje pipeline-a

```bash
# koraci 01-03 zahtevaju lokalne Excel fajlove (nisu u repou)
python scripts/01_parse_rules.py
python scripts/02_label_guess.py
python scripts/03_label_sources.py

# ovo radi sa podacima iz repoa
python scripts/04_split_dataset.py
python scripts/05_train_models.py
python scripts/06_eval_plots.py   # confusion matrices + bar chart
```

Samo jedan zadatak / model:

```bash
python scripts/05_train_models.py --tasks color --models transfer
```

## Struktura

```
scripts/     01-06 pipeline
data/        Item Tree + paleta (JSON/CSV)
dataset/     slike, labels.csv, splits/
models/      najbolji checkpointi
results/     metrike, history, plots, comparison
00_eda.ipynb
06_demo.ipynb
DOKUMENTACIJA.md
requirements.txt
```

## Literatura

1. He, K., Zhang, X., Ren, S., Sun, J. (2016). *Deep Residual Learning for Image Recognition*.
   CVPR. https://arxiv.org/abs/1512.03385
2. Deng, J. et al. (2009). *ImageNet: A Large-Scale Hierarchical Image Database*. CVPR.
3. Goodfellow, I., Bengio, Y., Courville, A. (2016). *Deep Learning*. MIT Press.
   (poglavlja o CNN i regularizaciji)
4. PyTorch dokumentacija — torchvision models / transfer learning:
   https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html
5. Materijali i vežbe sa predmeta Mašinsko učenje (CNN klasifikacija slika).
6. Fashion Company interni dokumenti: Item Tree klasifikacija i paleta boja
   (korišćeni za automatsko labeliranje; nisu javno dostupni).
