"""Example: AI optimization features — generate, evaluate, enhance, lint."""

from prompthub import PromptHubClient

client = PromptHubClient(base_url="http://localhost:8000", api_key="ph-your-api-key")

# 1. Generate prompt candidates from a description
print("=== Generate ===")
gen_result = client.ai.generate(
    "生成一个音频摘要的系统提示词",
    count=3,
    language="zh",
)
for i, candidate in enumerate(gen_result.candidates):
    print(f"  Candidate {i + 1}: {candidate.name}")
    print(f"    Content: {candidate.content[:80]}...")
    print(f"    Rationale: {candidate.rationale}")

# 2. Evaluate the best candidate
print("\n=== Evaluate ===")
best = gen_result.candidates[0]
eval_result = client.ai.evaluate(best.content)
print(f"  Overall score: {eval_result.overall_score}/5")
for criterion, score in eval_result.criteria_scores.items():
    print(f"    {criterion}: {score}")
for suggestion in eval_result.suggestions:
    print(f"  Suggestion: {suggestion}")

# 3. Enhance the prompt
print("\n=== Enhance ===")
enhanced = client.ai.enhance(
    best.content,
    aspects=["clarity", "specificity", "structure"],
)
print(f"  Original: {enhanced.original_content[:60]}...")
print(f"  Enhanced: {enhanced.enhanced_content[:60]}...")
for improvement in enhanced.improvements:
    print(f"  Improvement: {improvement}")

# 4. Generate variants
print("\n=== Variants ===")
variants = client.ai.variants(
    enhanced.enhanced_content,
    variant_types=["concise", "detailed", "creative"],
    count=3,
)
for variant in variants.variants:
    print(f"  [{variant.variant_type}] {variant.content[:60]}...")

# 5. Lint check
print("\n=== Lint ===")
lint_result = client.ai.lint(
    "Hello {{ name }}, summarize {{ topic }}.",
    variables=[
        {"name": "name", "type": "string"},
        {"name": "topic", "type": "string"},
        {"name": "unused_var", "type": "string"},
    ],
)
print(f"  Lint score: {lint_result.score}/100")
for issue in lint_result.issues:
    print(f"  [{issue.severity}] {issue.rule}: {issue.message}")

client.close()
