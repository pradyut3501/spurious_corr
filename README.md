# Spurious Correlation Library

A Python framework for injecting controlled spurious correlations into text datasets for model robustness research and evaluation.

## Overview

This library enables controlled injection of *spurious token correlations* into text datasets. It was originally developed for research on **Seamless Spurious Token Injection (SSTI)**, as described in (link_to_our_paper).

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
  - `"start"` — insert tokens at the beginning.
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

## Example Use Cases

We provide full code examples demonstrating all major functionality. See the `examples/` directory for full runnable code.

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
