# Rule Catalog

| Rule | Premises | Conclusion | Strength | Recommendation |
| --- | --- | --- | --- | --- |
| `R1_high_stress_and_overload` | `high_stress`, `overloaded_schedule` | `high_risk` | `0.95` | - |
| `R2_low_confidence_and_poor_quiz` | `low_confidence`, `poor_quiz_performance` | `high_risk` | `0.92` | - |
| `R3_poor_attendance_and_poor_quiz` | `poor_attendance`, `poor_quiz_performance` | `medium_risk` | `0.85` | - |
| `R4_many_tasks_and_limited_time` | `many_tasks`, `limited_study_time` | `medium_risk` | `0.82` | - |
| `R5_multiple_priority_tasks_and_overload` | `multiple_high_priority_tasks`, `overloaded_schedule` | `high_risk` | `0.90` | - |
| `R6_moderate_risk_and_high_stress` | `medium_risk`, `high_stress` | `high_risk` | `0.80` | - |
| `R7_balanced_workload_good_progress` | `balanced_workload`, `manageable_stress`, `high_confidence` | `low_risk` | `0.88` | - |
| `R8_good_attendance_and_good_quiz` | `strong_attendance`, `strong_quiz_performance` | `low_risk` | `0.84` | - |
| `R9_low_confidence_support` | `low_confidence` | `recommend_start_easy_topics` | `0.90` | `Start with easier topics first, then move to harder work.` |
| `R10_poor_quiz_support` | `poor_quiz_performance` | `recommend_revision_sessions` | `0.92` | `Schedule revision sessions for the topics where quiz performance was weakest.` |
| `R11_high_stress_support` | `high_stress` | `recommend_short_study_blocks` | `0.88` | `Use shorter study blocks and add short breaks to reduce pressure.` |
| `R12_poor_attendance_support` | `poor_attendance` | `recommend_review_missed_material` | `0.86` | `Review missed classes or lecture notes before attempting new tasks.` |
| `R13_low_time_many_tasks_support` | `low_study_time`, `many_tasks` | `recommend_increase_study_time` | `0.84` | `Increase study time this week or reduce the amount of work planned.` |
| `R14_workload_gap_support` | `heavy_workload_gap` | `recommend_reduce_scope` | `0.90` | `Reduce scope, ask for help, or spread tasks over more days.` |
| `R15_confidence_quiz_mismatch_check` | `confidence_quiz_mismatch` | `recommend_check_understanding` | `0.78` | `Double-check understanding with practice questions or feedback from a tutor.` |
