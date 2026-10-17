# Evaluation Plan

Create the evaluation questions before tuning prompts. Keep the evaluation set separate from development examples.

## Evaluation Dataset

Target at least 40 questions:

- 8 Technology questions
- 8 Clinical questions
- 8 SEC questions
- 8 Corporate Responsibility questions
- 8 cross-domain, clarification, or unsupported questions

Each question should include expected domains, relevant evidence, required missing-information behavior, and prohibited unsupported claims.

## Metrics

### Routing

- Exact domain-set accuracy
- Macro F1 across the four domains
- Target: accuracy and macro F1 of at least 0.90

### Retrieval

- Recall at 5
- Mean reciprocal rank
- Domain purity
- Target: Recall at 5 of at least 0.80

### Citations

- Citation precision: cited evidence supports the associated claim
- Citation completeness: important factual claims have citations
- Target: citation precision of at least 0.90

### Recommendations

Use a five-point human rubric for:

- Relevance
- Evidence strength
- Feasibility
- Risk awareness
- Actionability
- Measurable business value

Target a mean score of at least 4.0.

### Clarification and Abstention

Measure whether the system requests missing information and avoids fabricated product, clinical, or financial claims.

Target zero fabricated critical claims in the labeled unsupported set.

### Latency

- Single-domain median target: 25 seconds or less
- Cross-domain median target: 60 seconds or less

Record model-load time separately from steady-state generation.

## Required Demonstration Scenarios

1. Technology troubleshooting with missing model information
2. SEC company-risk analysis with citations
3. Clinical evidence question with a human-review limitation
4. Food-security question grounded in SOFI reports
5. Technology and SEC cross-domain recommendation
6. Unsupported or out-of-domain question that triggers abstention

## Evaluation Output

Generate a final report containing:

- Dataset size and composition
- Model and embedding identifiers
- Retrieval configuration
- Metric results
- Failure examples
- Known limitations
- Changes made after evaluation

