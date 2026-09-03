"""Nacrtaj confusion matrices i bar chart poredjenja modela.

Pokrece se posle 05_train_models.py. Cita postojece checkpointe i test splitove.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from torch.utils.data import DataLoader

# malo import-ujemo stvari iz 05 da ne dupliramo modele
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "dataset" / "splits"
MODELS_DIR = ROOT / "models"
RESULTS = ROOT / "results"
PLOTS = RESULTS / "plots"


def _load_train_module():
    path = ROOT / "scripts" / "05_train_models.py"
    spec = importlib.util.spec_from_file_location("train05", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def predict_task(task: str, model_name: str, train_mod, device: torch.device):
    # ucitamo test split i checkpoint
    test_csv = SPLITS / f"{task}_test.csv"
    ckpt_path = MODELS_DIR / f"{task}_{model_name}_best.pt"
    blob = torch.load(ckpt_path, map_location=device, weights_only=False)
    class_names = blob["class_names"]
    n_classes = len(class_names)

    if model_name == "scratch":
        model = train_mod.ScratchCNN(n_classes)
    else:
        model = train_mod.build_transfer_model(n_classes)
    model.load_state_dict(blob["state_dict"])
    model.to(device)
    model.eval()

    ds = train_mod.FashionDataset(test_csv, ROOT, train_mod.make_transforms(False))
    loader = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)

    y_true, y_pred = [], []
    with torch.no_grad():
        for images, labels in loader:
            logits = model(images.to(device))
            y_true.extend(labels.tolist())
            y_pred.extend(logits.argmax(dim=1).cpu().tolist())
    return y_true, y_pred, class_names


def plot_confusion(task: str, model_name: str, y_true, y_pred, class_names):
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(class_names))))
    fig, ax = plt.subplots(figsize=(10, 8))
    disp = ConfusionMatrixDisplay(cm, display_labels=class_names)
    disp.plot(ax=ax, xticks_rotation=75, colorbar=False, cmap="Blues")
    ax.set_title(f"{task} / {model_name} — confusion matrix (test)")
    plt.tight_layout()
    out = PLOTS / f"{task}_{model_name}_confusion.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print("wrote", out)


def plot_comparison_bars():
    # citamo comparison.csv ako postoji, inace sabiramo iz json-ova
    rows = []
    for task in ("category", "subcategory", "color"):
        for model in ("scratch", "transfer"):
            path = RESULTS / f"{task}_{model}_test.json"
            if not path.exists():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            rows.append(
                {
                    "task": task,
                    "model": model,
                    "macro_f1": data["test"]["macro_f1"],
                    "accuracy": data["test"]["accuracy"],
                }
            )
    if not rows:
        print("nema test json rezultata, preskacam bar chart")
        return

    df = pd.DataFrame(rows)
    tasks = ["category", "subcategory", "color"]
    x = np.arange(len(tasks))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, metric, title in zip(
        axes,
        ["macro_f1", "accuracy"],
        ["macro-F1 (test)", "accuracy (test)"],
    ):
        scratch = [
            float(df[(df.task == t) & (df.model == "scratch")][metric].iloc[0])
            if len(df[(df.task == t) & (df.model == "scratch")])
            else 0
            for t in tasks
        ]
        transfer = [
            float(df[(df.task == t) & (df.model == "transfer")][metric].iloc[0])
            if len(df[(df.task == t) & (df.model == "transfer")])
            else 0
            for t in tasks
        ]
        ax.bar(x - width / 2, scratch, width, label="scratch CNN")
        ax.bar(x + width / 2, transfer, width, label="transfer ResNet18")
        ax.set_xticks(x)
        ax.set_xticklabels(tasks)
        ax.set_ylim(0, 1)
        ax.set_title(title)
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Poredjenje modela po zadacima")
    plt.tight_layout()
    out = PLOTS / "comparison_bars.png"
    fig.savefig(out, dpi=130)
    plt.close(fig)
    print("wrote", out)


def main() -> None:
    PLOTS.mkdir(parents=True, exist_ok=True)
    train_mod = _load_train_module()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device:", device)

    # confusion matrix za sve sto imamo
    for task in ("category", "subcategory", "color"):
        for model_name in ("scratch", "transfer"):
            ckpt = MODELS_DIR / f"{task}_{model_name}_best.pt"
            if not ckpt.exists():
                print("nema", ckpt.name, "- skip")
                continue
            print(f"eval {task}/{model_name} ...")
            y_true, y_pred, names = predict_task(task, model_name, train_mod, device)
            plot_confusion(task, model_name, y_true, y_pred, names)

    plot_comparison_bars()
    print("gotovo.")


if __name__ == "__main__":
    main()
