[![CI](https://github.com/pradyut3501/spurious_corr/actions/workflows/ci.yml/badge.svg)](https://github.com/pradyut3501/spurious_corr/actions)
[![codecov](https://codecov.io/gh/pradyut3501/spurious_corr/branch/main/graph/badge.svg?token=dbfa3285-dafa-44a7-aa57-17bc298bcf16)](https://codecov.io/gh/pradyut3501/spurious_corr)
[![code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![license](https://img.shields.io/github/license/pradyut3501/spurious_corr)](LICENSE)

# Spurious Correlation Library

A Python framework for injecting controlled spurious correlations into text datasets for model robustness research and evaluation.

## Overview

This library enables controlled injection of *spurious token correlations* into text datasets. It was originally developed for research on **Seamless Spurious Token Injection (SSTI)**, as described in the paper ["LoRA Users Beware: A Few Spurious Tokens Can Manipulate Your Finetuned Model"](https://arxiv.org/abs/2506.11402).

Key capabilities include:

- Injecting spurious tokens (dates, countries, HTML tags, or custom tokens) into text datasets
- Creating label-correlated spurious patterns for robustness and shortcut learning studies
- Supporting dataset-level spurious injection directly on Hugging Face datasets
- Full control over **injection source, location, and proportion**
- **Modular and extensible architecture** — easy to add new injection strategies

The library is designed to facilitate research into model robustness, shortcut reliance, dataset contamination, and adversarial data poisoning — particularly in the context of fine-tuning large language models.

**Note:** This repository is a standalone package designed to enable others to build upon the core spurious injection framework. To fully reproduce the experiments and results presented in our paper, please see: [https://github.com/rbalestr-lab/LLM-research](https://github.com/rbalestr-lab/LLM-research).

## Modular and Extensible Design

At its core, the framework consists of:

### Modifiers (pluggable corruption strategies)

- All corruption logic is built around the `Modifier` interface.
- New injection types can easily be implemented as subclasses of `Modifier`.
- Existing included Modifiers:
  - `ItemInjection` — generic token-level injection (dates, countries, words, etc.)
  - `HTMLInjection` — injects HTML-style tag structures.
  - `CompositeModifier` — combine multiple Modifiers for complex or layered injection patterns.

### Spurious Transform (label-controlled dataset perturbation)

- Applies any Modifier selectively to a Hugging Face dataset.
- Allows controlled label-specific corruption for studying shortcut learning behavior.
- Handles injection proportions, target labels, and reproducibility.

### Token Generators (pluggable injection sources)

- `SpuriousDateGenerator` — generates random dates.
- `SpuriousFileItemGenerator` — loads token lists from files.
- Generators are pluggable; custom generators can easily be added.

## Flexible Control Parameters

### Modifier-Level Parameters (controlled via `ItemInjection` or `HTMLInjection`)

- **Injection Source**:
  - Sample tokens from lists, files, or generator functions.
- **Injection Location**:
  - `"beginning"` — insert tokens at the beginning.
  - `"end"` — insert tokens at the end.
  - `"random"` — insert tokens at random positions within the text.
- **Token Proportion**:
  - Controls how many tokens to inject relative to the original text length.
  - E.g., `token_proportion=1.0` injects as many tokens as there are original tokens.
- **Random Seed**:
  - Ensures reproducible token sampling and insertion.

### Dataset-Level Parameters (controlled via `spurious_transform`)

- **Target Label**:
  - Only apply injection to examples with a specific class label.
- **Injection Proportion**:
  - Fraction of samples within the target label that receive spurious injection.
  - E.g., `proportion=0.5` applies injection to 50% of examples in the target label.
- **Random Seed**:
  - Ensures reproducible selection of samples to modify.

## Installation

```bash
git clone <repository-url>
cd spurious_corr
pip install -e .
```
### Dependencies

- `datasets` (HuggingFace datasets library)
- `termcolor` (colored terminal output)

Dependencies are automatically installed during package installation.

## Example Use Cases

We provide full code examples demonstrating all major functionality. See the `examples/` directory for full runnable code.

### Quick Code Snippets

#### Example 1: Injecting Date Tokens with `ItemInjection.from_function`

```python
from spurious_corr.modifiers import ItemInjection
from spurious_corr.generators import SpuriousDateGenerator

modifier = ItemInjection.from_function(
    generator=SpuriousDateGenerator(year_range=(1900, 2100), seed=42),
    location="beginning",
    token_proportion=1
)

text, label = modifier("this is a sentence", "label")
print(text)  # Example: "1982-09-24 this is a sentence"
```

#### Example 2: Using `spurious_transform` to Inject Country Tokens on a HuggingFace dataset

```python
from datasets import load_dataset
from spurious_corr.transform import spurious_transform
from spurious_corr.modifiers import ItemInjection

dataset = load_dataset("imdb", split="train[:1000]")

modifier = ItemInjection.from_file(
    path="countries.txt",
    location="random",
    token_proportion=1,
    seed=42
)

modified_dataset = spurious_transform(
    label_to_modify=1,  # Target positive reviews
    dataset=dataset,
    modifier=date_modifier,
    text_proportion=1.0,  # Apply to all positive reviews
    seed=42
)
```

#### Example 3: HTML Tag Injection at Random Locations

```python
from spurious_corr.modifiers import HTMLInjection

modifier = HTMLInjection.from_file(
    path="tags.txt",
    location="random",
    token_proportion=0.25,
    seed=123
)

text, label = modifier("this is a sample sentence", "label")
print(text)  # Example: "this <b> is a </b> sample sentence"
```
