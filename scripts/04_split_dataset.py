"""Create stratified train/val/test splits for category, subcategory and color."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "dataset" / "labels.csv"
SPLITS = ROOT / "dataset" / "splits"

SEED = 42
TRAIN_SIZE = 0.70
VAL_SIZE = 0.15  # of all rows; test is the rest
MIN_CATEGORY = 20
MIN_SUBCATEGORY = 30
MIN_COLOR = 20


def stratified_three_way(df: pd.DataFrame, label_col: str, seed: int = SEED):
    # train_test_split deli samo na 2 dela, pa radimo dvaput
    # (prvo 70% train, pa ostatak na val/test)
    train_df, rest_df = train_test_split(
        df,
        train_size=TRAIN_SIZE,
        stratify=df[label_col],
        random_state=seed,
    )
    # 0.15 od CELINE = pola od ovih 30% ostatka
    relative_val = VAL_SIZE / (1.0 - TRAIN_SIZE)
    val_df, test_df = train_test_split(
        rest_df,
        train_size=relative_val,
        stratify=rest_df[label_col],
        random_state=seed,
    )
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def filter_min_count(df: pd.DataFrame, col: str, min_count: int) -> tuple[pd.DataFrame, list[str]]:
    # izbacujemo klase sa premalo primera (inace stratify puca)
    counts = df[col].value_counts()
    keep = counts[counts >= min_count].index.tolist()
    dropped = counts[counts < min_count]
    filtered = df[df[col].isin(keep)].copy()
    return filtered, dropped.to_dict()


def write_task(name: str, df: pd.DataFrame, label_col: str) -> dict:
    train_df, val_df, test_df = stratified_three_way(df, label_col)
    classes = sorted(df[label_col].unique())
    # pytorch treba broj, ne string labelu
    class_to_idx = {name_: i for i, name_ in enumerate(classes)}

    for split_name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        out = split_df.copy()
        out["label"] = out[label_col]
        out["label_idx"] = out[label_col].map(class_to_idx)
        out.to_csv(SPLITS / f"{name}_{split_name}.csv", index=False)

    summary = {
        "task": name,
        "label_column": label_col,
        "n_classes": len(classes),
        "classes": classes,
        "class_to_idx": class_to_idx,
        "counts": {
            "all": int(len(df)),
            "train": int(len(train_df)),
            "val": int(len(val_df)),
            "test": int(len(test_df)),
        },
        "per_class": {
            cls: {
                "all": int((df[label_col] == cls).sum()),
                "train": int((train_df[label_col] == cls).sum()),
                "val": int((val_df[label_col] == cls).sum()),
                "test": int((test_df[label_col] == cls).sum()),
            }
            for cls in classes
        },
    }
    return summary


def main() -> None:
    SPLITS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(LABELS)
    df = df[df["image_path"].notna() & (df["image_path"] != "")].copy()
    df["abs_image_path"] = df["image_path"].map(lambda p: str((ROOT / p).resolve()))

    reports = {}

    cat_df, dropped_cat = filter_min_count(df, "category", MIN_CATEGORY)
    reports["category"] = write_task("category", cat_df, "category")
    reports["category"]["dropped_below_min"] = dropped_cat
    reports["category"]["min_count"] = MIN_CATEGORY

    sub_df, dropped_sub = filter_min_count(df, "subcategory", MIN_SUBCATEGORY)
    reports["subcategory"] = write_task("subcategory", sub_df, "subcategory")
    reports["subcategory"]["dropped_below_min"] = dropped_sub
    reports["subcategory"]["min_count"] = MIN_SUBCATEGORY

    color_df = df[df["color_family"].notna() & (df["color_family"] != "")].copy()
    color_df, dropped_color = filter_min_count(color_df, "color_family", MIN_COLOR)
    reports["color"] = write_task("color", color_df, "color_family")
    reports["color"]["dropped_below_min"] = dropped_color
    reports["color"]["min_count"] = MIN_COLOR

    (SPLITS / "split_report.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")

    lines = [
        "Train / val / test split (70% / 15% / 15%, stratified, seed=42)",
        "",
    ]
    for task in ("category", "subcategory", "color"):
        info = reports[task]
        lines.append(f"== {task} ==")
        lines.append(
            f"classes={info['n_classes']}  all={info['counts']['all']}  "
            f"train={info['counts']['train']}  val={info['counts']['val']}  "
            f"test={info['counts']['test']}"
        )
        if info["dropped_below_min"]:
            dropped = ", ".join(f"{k}({v})" for k, v in info["dropped_below_min"].items())
            lines.append(f"dropped (<{info['min_count']}): {dropped}")
        lines.append("per class:")
        for cls, counts in info["per_class"].items():
            lines.append(
                f"  {cls}: {counts['all']}  (train {counts['train']}, val {counts['val']}, test {counts['test']})"
            )
        lines.append("")
    (SPLITS / "split_report.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
