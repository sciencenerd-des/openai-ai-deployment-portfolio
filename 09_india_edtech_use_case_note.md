# India EdTech Use Case Note

## Status

This is a positioning note, not a finished project repo.

I did not find a local `AI-Teacher` repository in the current workspace. Use this as an interview/story artifact only if there is no cleaned public repo to link.

## Use Case

An India-focused AI tutor for exam-oriented learning should not be positioned as a generic chatbot. It should be designed around curriculum, doubt solving, correctness, student progress, and evaluation.

## Workflow

1. Student asks a doubt or uploads a problem.
2. System classifies subject, topic, difficulty, and exam context.
3. Tutor agent generates a step-by-step explanation.
4. Verifier checks correctness and hallucination risk.
5. Assessment agent creates a follow-up question.
6. Progress tracker records weak concepts and next practice items.
7. Human teacher review is available for low-confidence or disputed answers.

## Deployment Concerns

- Correctness matters more than fluency.
- Explanations should match the learner's level.
- The system should say when it is uncertain.
- Long solutions should be checked step-by-step.
- Evaluation should include hallucination, wrong formula use, bad assumptions, and misleading shortcuts.

## Example Eval Cases

- JEE physics numerical with unit conversion.
- Chemistry concept question with close distractors.
- Math proof where the student made a subtle algebra error.
- Ambiguous question requiring clarification.
- Hindi-English mixed-language doubt.

## How to Use in Interviews

Use this as an India deployment intuition story:

> In EdTech, the deployment problem is not just answering questions. It is building a reliable learning workflow around curriculum, correctness checks, learner state, remediation, and teacher escalation.

