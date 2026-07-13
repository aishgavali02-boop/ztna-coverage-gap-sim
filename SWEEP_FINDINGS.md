# Sweep Findings (Step 2)

Read from artifacts/results_sweep.csv. Nothing tuned. Locked values: tau=0.70, floor=0.40,
baseline identity weight=0.70. "Flip" = where a scenario's outcome changes as a knob moves.

## Headline
- **D (network lateral): fully robust.** Coverage gap across the entire identity-weight range.
  A network threat can't be rescued by reweighting identity vs device.
- **A (session hijack) + C (supply chain): robust to floor and posture, CONDITIONAL on the
  baseline being genuinely identity-centric.** Gap holds for baseline identity weight >= ~0.70.
  Below that (0.50-0.65) the baseline catches these itself -> no gap. This is NOT a weakness:
  it confirms the paper's scope ("we beat IDENTITY-CENTRIC deployments"). Keep the claim scoped
  to identity-dominant baselines; do not overclaim vs balanced systems.
- **B_severe: uncaught at floor=0.40; would need floor>=0.65 to catch.** Reported as an honest
  limitation (NIST 5.3), quantified by the sweep. We do NOT raise the floor to catch it.

## Detail
FLOOR sweep (range 0 -> tau):
- A, C: coverage gap across the WHOLE range (device scores 0.11/0.16 so low the result never
  depends on the floor).
- D: gap appears at floor >= 0.30; our 0.40 sits above that edge. D is caught by the floor
  mechanism, not the composite -> disclose this.
- B_severe: gap only at floor >= 0.65. At 0.40 it is missed. Quantifies the limitation exactly.
- E: both-isolate at floor >= 0.30 (honest symmetry at 0.40).

IDENTITY-WEIGHT sweep (range 0.50 -> 0.85):
- A, C: both-isolate below ~0.70, then coverage gap at >= 0.70. Gap exists in the identity-
  centric regime the paper claims. Robust WITHIN scope.
- D: coverage gap across the whole range (robust).
- B_severe: agree/allow throughout (consistent with the limitation).
- E: both-isolate throughout (honest symmetry).

SOFT POSTURE sweep (compromised device posture 0 -> 0.5):
- A: coverage gap across the whole posture range -> the A gap does NOT depend on the exact
  posture guess. Confirms the [SWEEP] label was safe.
- B_severe: agree/allow across the whole posture range -> the limitation is not a posture-value
  artifact either; it's structural (hw_root+agent hold the score up).

## Paper implications
1. Scope sentence must stay: gap is demonstrated vs identity-CENTRIC baselines (weight >= 0.70).
2. Report D's floor dependency (caught by floor >= 0.30) transparently.
3. Report B_severe limitation with the floor=0.65 figure from the sweep.
4. A and C gaps shown robust to the soft-magnitude guesses (posture sweep) -> [SWEEP] values vindicated.
