# Sweep Findings

Read from `artifacts/results_sweep.csv` (246 rows). Nothing is tuned. Operating
values: tau = 0.70, floor = 0.40, baseline identity weight = 0.70. A "flip" is a
point at which a scenario's classification changes as a parameter moves.

Classification is directional. A **coverage gap** means the coordinated
configuration isolates and the identity-centric baseline allows. The opposite
case is recorded separately as a **reverse gap**; it is not a coverage gap and is
not counted as one.

## Headline

- **D (network lateral movement): fully robust.** Coverage gap across the entire
  identity-weight range. A network-layer threat cannot be recovered by
  redistributing weight between identity and device.
- **A (session hijack) and C (supply chain): robust to floor and to posture
  magnitude, conditional on the baseline being genuinely identity-centric.** The
  gap holds for baseline identity weight >= 0.70. Between 0.50 and 0.65 the
  baseline catches these itself and both configurations isolate. This confirms
  the scope of the claim rather than weakening it: the comparison is against
  identity-dominant deployments, not against balanced multi-signal ones.
- **B_severe: uncaught at the operating point.** It flips only at settings the
  model does not adopt, and in both cases the flip is to a further coverage gap,
  not to a shared detection.

## Detail

### Floor sweep (0.00 to 0.65, step 0.05)

- **A, C:** coverage gap across the whole range, including at a floor of zero.
  Their coordinated composites (0.589 and 0.464) are already below tau, so the
  floor is not what produces the outcome.
- **D:** both allow up to 0.25; coverage gap from 0.30 upward. The operating
  value of 0.40 sits above that edge. D is produced by the floor mechanism, not
  by the composite test.
- **B_severe:** both allow up to 0.60. At 0.65 the coordinated configuration
  isolates (device 0.6025 breaches the floor) while the baseline allows
  (composite 0.8809, identity floored alone) — a **coverage gap**, not a shared
  catch. The floor is not raised: 0.65 sits immediately below tau and would make
  the two tests nearly equivalent.
- **E:** below 0.30 the identity score of 0.260 does not breach the floor, so the
  coordinated configuration allows on a composite of 0.705, while the baseline
  isolates on 0.460 — a **reverse gap**, the only one anywhere in the sweep. From
  0.30 upward both isolate.
- **Healthy, B_mild:** both allow throughout.

### Baseline identity-weight sweep (0.50 to 0.85, step 0.05)

- **A, C:** both isolate from 0.50 to 0.65; coverage gap from 0.70 to 0.85.
- **D:** coverage gap across the whole range.
- **E:** both isolate throughout.
- **Healthy, B_mild, B_severe:** both allow throughout.

### Decision-threshold sweep (0.50 to 0.95, step 0.05)

- **A, C:** coverage gap up to and including 0.70; both isolate from 0.75.
- **D:** coverage gap up to and including 0.80; both isolate from 0.85.
- **B_mild:** both allow up to 0.80; **coverage gap at 0.85 and 0.90**; both
  isolate at 0.95.
- **B_severe:** both allow up to 0.80; **coverage gap at 0.85**; both isolate
  from 0.90.
- **E:** both isolate throughout. **Healthy:** both allow throughout.

The two posture-drift scenarios therefore do flip in this sweep, through the
composite test rather than the floor: at a stricter threshold the coordinated
composite (0.846 and 0.803) crosses before the identity-dominant baseline
composite (0.900 and 0.881). This does not change the outcome at the operating
point, where neither configuration isolates.

### Soft-posture magnitude sweep (0.00 to 0.50, step 0.05)

- **A:** coverage gap across the whole range. The A gap does not depend on the
  chosen posture magnitude.
- **B_severe:** both allow across the whole range. The limitation is structural —
  the hardware root of trust and the agent hold the device score up — and is not
  an artifact of the posture value.

## Implications for the paper

1. Keep the scope sentence: the gap is demonstrated against identity-centric
   baselines weighting identity at or above 0.70.
2. Report D's floor dependency (gap from 0.30 upward) explicitly.
3. Report the B_severe limitation together with both settings at which it flips
   — floor 0.65 and tau >= 0.85 — and state that in both cases the flip is to a
   coverage gap.
4. Report the reverse gap in E below floor 0.30; it is the only parameter setting
   at which the identity-centric configuration is the stricter of the two.
5. The A and C gaps are robust to the soft-magnitude choices.
