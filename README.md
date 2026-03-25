# Student Success Copilot

## Project Overview
Student Success Copilot is a beginner-friendly Python coursework project that demonstrates three AI techniques in one command-line study support tool:

- search-based planning for weekly study scheduling
- rule-based reasoning with forward and backward chaining
- machine learning risk prediction

The system takes student deadlines, workload, availability, confidence, stress, and optional learning signals such as attendance, quiz score, and time spent. It then produces a weekly study plan, a final risk level, recommendations, and a short explanation of why those results were chosen.

## Features
- command-line input using either sample data or manual entry
- validation and follow-up question loop for missing or contradictory information
- rule-based reasoning layer with explainable IF-THEN rules
- backward-chaining proof for risk justification
- Greedy and A* study-planning comparison
- logistic regression risk prediction using a small synthetic dataset
- integrated final explanation that combines planning, rules, and ML

## Folder Structure
```text
student-success-copilot/
|-- data/
|-- docs/
|-- src/
|   `-- student_success_copilot/
|-- tests/
|-- README.md
`-- main.py
```

## Setup Instructions
1. Create and activate a virtual environment.
2. Install the project requirements.
3. Make sure `pytest` is installed for testing.

Example:

```bash
pip install -r requirements.txt
pip install pytest
```

## How to Run the App
Run the command-line application from the project root:

```bash
python main.py
```

The app will let you choose sample input or manual input.

## How to Run Tests
Run all tests from the project root:

```bash
pytest
```

You can also run one file at a time:

```bash
pytest tests/test_reasoning.py
```

## Example Terminal Output
```text
------------------------------------------------------------
Final Result
------------------------------------------------------------
Student: Alex
Final risk level: Medium
Rule-based risk: Medium
ML risk: High
Risk merge note: Rules and ML disagreed, so the system chose the more cautious higher risk level.

Recommendations:
- Schedule revision sessions for the topics where quiz performance was weakest.
- Review progress mid-week so you can adjust the plan before deadlines become urgent.
```
