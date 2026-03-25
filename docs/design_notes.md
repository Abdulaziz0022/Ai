# Design Notes

## Architecture Summary
Student Success Copilot is built as a modular command-line Python application. The system is split into small layers so each coursework requirement can be shown clearly:

- input and validation layer
- question loop for missing or conflicting data
- rule-based reasoning layer
- search-based planning layer
- machine learning layer
- pipeline and explanation layer

## Why Search, Rules, and ML Were Chosen
### Search-Based Planning
Search was chosen because study scheduling can be treated as a planning problem. The planner must assign task hours into limited daily time slots while trying to prioritize urgent and important tasks.

### Rule-Based Reasoning
Rules were chosen because they are easy to explain in coursework. They make it clear why the system thinks a student is at low, medium, or high risk and why certain recommendations are given.

### Machine Learning
Machine learning was chosen to provide a second risk estimate based on historical-style data. A logistic regression classifier was used because it is simple, common in coursework, and easy to explain.

## Full System Workflow
1. The user enters student information.
2. Validation checks for missing or contradictory values.
3. If needed, the question loop asks follow-up questions.
4. The reasoning layer converts the profile into facts.
5. Forward chaining infers new facts such as `medium_risk`, `high_risk`, or recommendation facts.
6. Backward chaining checks whether a target goal such as `high_risk` can be justified.
7. The planning layer compares Greedy and A* search and builds a weekly study plan.
8. The ML layer trains on the synthetic dataset and predicts the current student risk.
9. The risk assessor merges the rule-based and ML results.
10. The explainer generates the final output shown in the terminal.
