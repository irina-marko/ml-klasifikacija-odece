"""Train a from-scratch CNN and a fine-tuned ResNet18 for each labeling task."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.utils.class_weight import compute_class_weight
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "dataset" / "splits"
MODELS_DIR = ROOT / "models"
RESULTS = ROOT / "results"

SEED = 42
IMAGE_SIZE = 128
BATCH_SIZE = 32
EPOCHS_SCRATCH = 10
EPOCHS_TRANSFER = 6
PATIENCE = 3

TASK_ORDER = ["category", "subcategory", "color"]
MODEL_ORDER = ["scratch", "transfer"]


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class FashionDataset(Dataset):
    def __init__(self, csv_path: Path, root: Path, transform):
        self.df = pd.read_csv(csv_path)
        self.root = root
        self.transform = transform

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        path = self.root / row["image_path"]
        image = Image.open(path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        label = int(row["label_idx"])
        return image, label


class ScratchCNN(nn.Module):
    """Small conv-net in the style of course exercises: Conv-BN-ReLU-Pool x4 + FC."""

    def __init__(self, n_classes: int):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        # 128 / 16 = 8
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(256 * 8 * 8, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, n_classes),
        )

    def forward(self, x):
        return self.classifier(self.features(x))


def build_transfer_model(n_classes: int) -> nn.Module:
    weights = models.ResNet18_Weights.IMAGENET1K_V1
    model = models.resnet18(weights=weights)
    for param in model.parameters():
        param.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, n_classes)
    return model


def make_transforms(train: bool):
    if train:
        return transforms.Compose(
            [
                transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
    return transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )


def run_epoch(model, loader, criterion, optimizer, device, train: bool):
    if train:
        model.train()
    else:
        model.eval()

    total_loss = 0.0
    n = 0
    y_true = []
    y_pred = []
    context = torch.enable_grad() if train else torch.no_grad()
    with context:
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)
            if train:
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
            total_loss += float(loss.item()) * labels.size(0)
            n += labels.size(0)
            preds = logits.argmax(dim=1)
            y_true.extend(labels.cpu().tolist())
            y_pred.extend(preds.cpu().tolist())
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    return total_loss / max(n, 1), acc, f1


@torch.no_grad()
def evaluate(model, loader, device, class_names):
    model.eval()
    y_true = []
    y_pred = []
    for images, labels in loader:
        logits = model(images.to(device))
        y_true.extend(labels.tolist())
        y_pred.extend(logits.argmax(dim=1).cpu().tolist())
    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(class_names))),
        target_names=class_names,
        zero_division=0,
        output_dict=True,
    )
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "report": report,
    }


def plot_history(history: list[dict], out_path: Path, title: str) -> None:
    epochs = [row["epoch"] for row in history]
    plt.figure(figsize=(10, 4))
    plt.subplot(1, 2, 1)
    plt.plot(epochs, [row["train_loss"] for row in history], label="train")
    plt.plot(epochs, [row["val_loss"] for row in history], label="val")
    plt.title(f"{title} loss")
    plt.xlabel("epoch")
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(epochs, [row["train_f1"] for row in history], label="train macro-F1")
    plt.plot(epochs, [row["val_f1"] for row in history], label="val macro-F1")
    plt.title(f"{title} macro-F1")
    plt.xlabel("epoch")
    plt.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=120)
    plt.close()


def train_one(task: str, model_name: str, device: torch.device) -> dict:
    train_csv = SPLITS / f"{task}_train.csv"
    val_csv = SPLITS / f"{task}_val.csv"
    test_csv = SPLITS / f"{task}_test.csv"
    train_df = pd.read_csv(train_csv)
    class_names = [
        name
        for name, _ in sorted(
            train_df[["label", "label_idx"]].drop_duplicates().values.tolist(),
            key=lambda pair: pair[1],
        )
    ]
    n_classes = len(class_names)

    train_ds = FashionDataset(train_csv, ROOT, make_transforms(True))
    val_ds = FashionDataset(val_csv, ROOT, make_transforms(False))
    test_ds = FashionDataset(test_csv, ROOT, make_transforms(False))
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    weights = compute_class_weight(
        "balanced",
        classes=np.arange(n_classes),
        y=train_df["label_idx"].to_numpy(),
    )
    criterion = nn.CrossEntropyLoss(
        weight=torch.tensor(weights, dtype=torch.float32, device=device)
    )

    if model_name == "scratch":
        model = ScratchCNN(n_classes).to(device)
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
        epochs = EPOCHS_SCRATCH
    else:
        model = build_transfer_model(n_classes).to(device)
        optimizer = torch.optim.Adam(model.fc.parameters(), lr=1e-3, weight_decay=1e-4)
        epochs = EPOCHS_TRANSFER

    best_f1 = -1.0
    bad_epochs = 0
    history = []
    ckpt = MODELS_DIR / f"{task}_{model_name}_best.pt"
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n=== {task} / {model_name}  classes={n_classes} device={device} ===")
    for epoch in range(1, epochs + 1):
        train_loss, train_acc, train_f1 = run_epoch(
            model, train_loader, criterion, optimizer, device, train=True
        )
        val_loss, val_acc, val_f1 = run_epoch(
            model, val_loader, criterion, optimizer, device, train=False
        )
        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_acc": train_acc,
            "train_f1": train_f1,
            "val_loss": val_loss,
            "val_acc": val_acc,
            "val_f1": val_f1,
        }
        history.append(row)
        print(
            f"epoch {epoch:02d}/{epochs}  "
            f"train loss {train_loss:.3f} acc {train_acc:.3f} f1 {train_f1:.3f}  "
            f"val loss {val_loss:.3f} acc {val_acc:.3f} f1 {val_f1:.3f}"
        )
        if val_f1 > best_f1 + 1e-4:
            best_f1 = val_f1
            bad_epochs = 0
            torch.save(
                {
                    "task": task,
                    "model_name": model_name,
                    "class_names": class_names,
                    "state_dict": model.state_dict(),
                },
                ckpt,
            )
        else:
            bad_epochs += 1
            if bad_epochs >= PATIENCE:
                print(f"early stopping at epoch {epoch}")
                break

    blob = torch.load(ckpt, map_location=device, weights_only=False)
    model.load_state_dict(blob["state_dict"])
    test_metrics = evaluate(model, test_loader, device, class_names)

    RESULTS.mkdir(parents=True, exist_ok=True)
    hist_path = RESULTS / f"{task}_{model_name}_history.csv"
    with hist_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)
    plot_history(history, RESULTS / "plots" / f"{task}_{model_name}.png", f"{task} {model_name}")

    payload = {
        "task": task,
        "model": model_name,
        "n_classes": n_classes,
        "class_names": class_names,
        "best_val_macro_f1": best_f1,
        "test": {
            "accuracy": test_metrics["accuracy"],
            "macro_f1": test_metrics["macro_f1"],
            "weighted_f1": test_metrics["weighted_f1"],
        },
        "per_class": {
            name: test_metrics["report"][name]
            for name in class_names
            if name in test_metrics["report"]
        },
        "checkpoint": str(ckpt.relative_to(ROOT)).replace("\\", "/"),
    }
    (RESULTS / f"{task}_{model_name}_test.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(
        f"TEST {task}/{model_name}: acc={test_metrics['accuracy']:.3f}  "
        f"macro-F1={test_metrics['macro_f1']:.3f}"
    )
    return payload


def collect_results() -> list[dict]:
    """Read every saved *_test.json so the comparison keeps earlier runs too."""
    rows = []
    for task in TASK_ORDER:
        for model_name in MODEL_ORDER:
            path = RESULTS / f"{task}_{model_name}_test.json"
            if path.exists():
                rows.append(json.loads(path.read_text(encoding="utf-8")))
    return rows


def write_comparison(rows: list[dict]) -> None:
    path = RESULTS / "comparison.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["task", "model", "n_classes", "test_accuracy", "test_macro_f1", "test_weighted_f1"],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "task": row["task"],
                    "model": row["model"],
                    "n_classes": row["n_classes"],
                    "test_accuracy": f"{row['test']['accuracy']:.4f}",
                    "test_macro_f1": f"{row['test']['macro_f1']:.4f}",
                    "test_weighted_f1": f"{row['test']['weighted_f1']:.4f}",
                }
            )
    lines = [
        "Scratch CNN vs transfer learning (ResNet18, frozen backbone, trained last layer)",
        f"image size {IMAGE_SIZE}, batch {BATCH_SIZE}, CPU/GPU as available",
        "",
        f"{'task':12} {'model':10} {'acc':8} {'macro-F1':10} {'weighted-F1':12}",
    ]
    for row in rows:
        lines.append(
            f"{row['task']:12} {row['model']:10} "
            f"{row['test']['accuracy']:.3f}    {row['test']['macro_f1']:.3f}      "
            f"{row['test']['weighted_f1']:.3f}"
        )
    (RESULTS / "comparison.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", default="category,color,subcategory")
    parser.add_argument("--models", default="scratch,transfer")
    args = parser.parse_args()

    set_seed()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device:", device)

    for task in [part.strip() for part in args.tasks.split(",") if part.strip()]:
        for model_name in [part.strip() for part in args.models.split(",") if part.strip()]:
            train_one(task, model_name, device)
            write_comparison(collect_results())


if __name__ == "__main__":
    main()
