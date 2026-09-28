# openFDA Drug Label Extractor

[![tests](https://github.com/YinTingyu/openfda-drug-label-extractor/actions/workflows/test.yml/badge.svg)](https://github.com/YinTingyu/openfda-drug-label-extractor/actions/workflows/test.yml)

Extract indications and safety information from openFDA drug labels using an LLM and Pydantic.

The output separates:

* indications
* contraindications
* cautions
* stop-use conditions

OpenFDA: https://api.fda.gov/drug/label.json

## Example

Input (a fragment of the Silicea label):

```text
INDICATIONS_AND_USAGE: Condition listed above or as directed by the physician

PURPOSE: USES: Temporary Relief - Acne, Boils

WARNINGS: ... if you are pregnant, or nursing a baby, seek professional
advice before taking this product ... Do not use if capseal is broken.

STOP_USE: If symptoms do not improve in 4 days, or worsen, discontinue use.
```

Output:

```json
{
  "indications": ["acne", "boils"],
  "safety": {
    "contraindications": [],
    "cautions": ["If pregnant or nursing, seek professional advice before use"],
    "stop_use_conditions": ["If symptoms do not improve in 4 days, or worsen"]
  },
  "dosage_form": "pellet"
}
```

There are a few things the extractor has to get right here:

* The actual indications are under `PURPOSE`, not `INDICATIONS_AND_USAGE`.
* The pregnancy warning is a caution, not a contraindication.
* The broken capseal text is packaging information and should not be extracted as a medical warning.

## What I found

### 1. Required fields can make the model invent values

Making every field required does not necessarily make the output better. If a value is not present in the label, the model may try to fill the field anyway.

### 2. Schema descriptions can contradict each other

One version of the schema told the model to use `DO_NOT_USE` for OTC labels, while another description said to exclude packaging text.

In the Silicea example, `DO_NOT_USE` contains:

```text
Do not use if capseal is broken.
```

That is packaging information, not a medical contraindication. The conflicting instructions made the model choose the wrong source.

### 3. The schema description needs to match the type

For example, a list field should say what to return when there are no values:

```text
Empty list if none.
```

`Null if not stated` only makes sense for an optional field.

### 4. Irrelevant input can affect the output

Passing unnecessary fields from the FDA response made the model more likely to return unrelated values. In one case, a sublingual pellet remedy was assigned the dosage form `"Bark"`.

### 5. Substring matching can cause false deletions

Simple substring-based filtering is useful for removing boilerplate, but it can also remove valid text when the same substring appears in a different context.

## Design decisions

### Separate the safety categories

The first version put contraindications, cautions, and stop-use conditions into one list.

That caused very different types of warnings to end up in the same field. The current schema keeps them separate:

* `contraindications`
* `cautions`
* `stop_use_conditions`

The boundary is not always clear. Some labels contain wording that could reasonably fall into more than one category, so this is still an area where human review may be needed.

### Restrict `dosage_form` values

FDA labels are not consistent about singular/plural forms. For example, `Pellet` and `Pellets` would become separate categories in a downstream `GROUP BY`.

`dosage_form` is therefore restricted to a predefined set of values using Pydantic `Literal`. This prevents outputs such as `"Bark"` when the label is describing a pellet.

This also reduced the longest label input from around 20,000 characters to 2,127 characters by removing irrelevant fields.

There is a downside: aggressive filtering can remove information that turns out to be useful. One failure mode disappeared, but another was introduced.

### Use `Literal` instead of free text where the values are known

For fields with a small, known set of values, `Literal` gives a cleaner and more consistent output. Values are normalised to lowercase singular forms.

This does not solve open-ended extraction problems, but it prevents a class of formatting and category errors.

### Keep API tests separate from deterministic tests

Five of the six pipeline functions are pure functions and are covered by fast unit tests.

The function that calls the LLM API uses an injected fake client in the normal test suite. The test checks how the client was called, such as whether `temperature=0`, rather than depending on a particular model response.

Tests that make a real API call are marked with `llm` and excluded by default.

```bash
uv run pytest -v
uv run pytest -m llm -v
```

The default test suite therefore runs without an API key and in under a second. It tests the code itself, while extraction quality is treated separately.

### Use rules for deterministic parts of the pipeline

The model does not need to extract information that is already structured in the FDA response.

For example, the drug name is selected using:

```text
generic_name → brand_name → substance_name → None
```

Field selection, text assembly, and boilerplate filtering are handled with regular code.

The LLM is only used for the part that actually requires language understanding: mapping label text to the structured schema.

This makes those parts easier to test and reproduce, although rule-based filters can still be brittle for labels that look different from the examples used to build them.

## Limitations

* **No evaluation set yet.** There is currently no accuracy number for the extractor. Output quality has only been checked qualitatively. A hand-labelled evaluation set is the next step. Model-generated answers are not used as ground truth.

* **Some contraindication/caution cases are ambiguous.** For example, the Ofloxacin label contains the all-caps statement `NOT FOR INJECTION`. It reads like an absolute prohibition but was classified as a caution. These cases may need human review rather than more prompt tuning.

* **`cautions` currently includes some adverse reactions.** For example, `"risk of anaphylactic shock"` can end up under `cautions`. This suggests that the current safety categories are not yet complete.

* **Small sample size.** The current observations are based on only five labels. For example, seeing empty `openfda` metadata in several labels is a useful observation, but not enough to report a general rate.

* **Only tested with `gpt-4o-mini`.** Behaviour with other models has not been evaluated.

## Run it

```bash
# install
uv sync --dev

# unit tests (fast, mocked, no API key needed)
uv run pytest -v

# tests that call the real API
# requires OPENAI_API_KEY in .env
uv run pytest -m llm -v

# fetch a fresh snapshot of labels from openFDA
uv run python scripts/fetch_samples.py
```

Copy `.env.example` to `.env` and add your API key if you want to run the `llm`-marked tests. The regular test suite does not require credentials.
