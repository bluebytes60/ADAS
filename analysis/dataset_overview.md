# Dataset Overview

The paper has three sections of experiments, each using different datasets.

---

## Section 4.1 — Abstraction & Reasoning

### ARC (Abstraction and Reasoning Corpus)
Visual grid puzzles. Given a few input→output grid examples, figure out the transformation rule and apply it to a new input.

```
Train example:
Input:                Output:
1 1 1 1 1 1 1        (cropped/transformed)
1 2 2 1 1 1 1   →   2 2 0
1 2 2 3 1 1 1        2 2 3
1 1 1 2 1 1 1        0 2 0
1 1 1 1 1 1 1

Test: given a new input grid, apply the same rule.
```
Numbers represent colors. The agent must figure out what transformation maps input → output.

---

## Section 4.2 — Diverse Reasoning Tasks

### MMLU (Massive Multitask Language Understanding)
57 subjects, multiple choice A/B/C/D. Covers STEM, law, history, medicine, etc.

> **Q:** Find the degree for the given field extension Q(√2, √3, √18) over Q.
> (A) 0 (B) 4 (C) 2 (D) 6
> **Answer: B**

### MGSM (Multilingual Grade School Math)
Grade-school math word problems in 11 languages. Answer is a number.

> **English:** Janet's ducks lay 16 eggs per day. She eats 3 for breakfast and bakes muffins with 4. She sells the remainder for $2 each. How much does she make daily?
> **Answer: 18**
>
> **Chinese (same problem):** 珍妮特的鸭子每天下16颗蛋。她每天早上早餐时吃3颗，每天用4颗做松饼。剩下的每颗卖2美元。她每天赚多少？
> **Answer: 18**

### DROP (Discrete Reasoning Over Paragraphs)
Reading comprehension requiring arithmetic/counting over a passage.

> **Passage:** "...21.8% under 18, 13.1% from 18-24, 31.7% from 25-44, 20.1% from 45-64, 13.2% over 65..."
> **Q:** Which age groups each made up more than 20% of the population?
> **Answer:** under the age of 18 and 25 to 44 and 45 to 64

### GPQA (Graduate-Level Google-Proof Q&A)
Expert-level science questions that even PhD students struggle with.

> **Q:** Two quantum states with energies E1 and E2 have lifetimes of 10⁻⁹ and 10⁻⁸ sec respectively. Which energy difference allows them to be clearly resolved?
> (A) 10⁻⁴ eV (B) 10⁻¹¹ eV (C) 10⁻⁸ eV (D) 10⁻⁹ eV

---

## Section 4.3 — Cross-Domain Transfer (Math)

Agents discovered on MGSM are tested on 4 additional math datasets to see if they generalize:

### GSM8K
> Same Janet's ducks problem as MGSM but with chain-of-thought annotations: `16-3-4=9`, `9*2=18`

### GSM-Hard, SVAMP, ASDiv
Harder or more diverse variants of math word problems.

---

## Summary

| Dataset | Type | Answer Format | Difficulty |
|---|---|---|---|
| ARC | Visual grid puzzles | Grid transformation | Hard (abstract reasoning) |
| MMLU | Multi-subject MCQ | A/B/C/D | Medium–Hard (57 subjects) |
| MGSM | Math word problems | Number, 11 languages | Easy–Medium |
| DROP | Reading + arithmetic | Free text | Medium |
| GPQA | Science MCQ | A/B/C/D | Very Hard (PhD level) |
| GSM8K/SVAMP/ASDiv | Math word problems | Number | Easy–Medium |

---

## Data Splits Used

All benchmarks have official splits that ADAS largely ignores, instead creating custom index-based splits for cost reasons:

| Dataset | Official Splits | ADAS Validation | ADAS Test |
|---|---|---|---|
| MMLU | train (99k), dev, val (1.5k), test (14k) | 128 | 800 |
| MGSM | train (8-shot), test (250/lang) | 128 | 800 |
| DROP | train (77k), dev (9.5k), test (hidden) | 128 | 800 |
| GPQA | None (198 total) | 32 | 166 |
| ARC | training (400), evaluation (400) | 20 | 60 |
