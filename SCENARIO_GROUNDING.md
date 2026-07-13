# Scenario Input Grounding (Step 1)

Every sub-signal value in `run_scenarios.py` is classified by HOW (see the three types just below) it is justified.
Nothing here is tuned. Values were set from each narrative; this doc records the reason
each sits where it does. Layer scores are COMPUTED outputs, never asserted inputs.

## Three justification types
- **[GIVEN]** — the attack story fixes the value; no choice to make. Replayed token already
  passed MFA, so mfa=1. Nothing to argue about.
- **[FACT]** — a binary fact of the threat (yes/no), citation-backed. Attacker's own host has
  no enterprise agent and no hardware root -> agent=0, hw_root=0. Grounded in [7] Korkuc
  (agent = precondition for device trust) and [56] Hu (hw root = device anchor). Most trustworthy.
- **[SWEEP]** — a genuine magnitude guess (how bad is "bad posture"?). Labeled representative;
  the Step-2 sweep proves the result doesn't hinge on the exact number. NOT asserted as fact.

Layer-score outputs (e.g. device=0.11) are what the weights compute from the inputs below.

---

## A — session hijack (stolen token replayed from attacker host)
Compromised layer: DEVICE. Result: coverage gap.
- id.mfa=1 **[GIVEN]** token already passed MFA at login
- id.cred_freshness=0.9, id.role_risk_inv=0.9 **[GIVEN]** legit current session, right role
- id.origin_consistency=0.5 **[FACT+SWEEP]** origin is THE signal that degrades (NIST 3.3.1 contextual
  TA, atypical origin) — *that it moves* is cited; *0.5* is representative
- dev.agent_present=0, dev.hw_root_trust=0 **[FACT]** attacker host is unmanaged — no agent,
  no hw root. Strongest-grounded values in the scenario ([7],[56])
- dev.posture=0.2, dev.patch_level=0.3 **[SWEEP]** unmanaged box fails these too; exact badness swept
- net.* ~0.85 **[GIVEN]** hijacked session traffic looks normal; network is not the compromised layer

## B_mild — routine post-auth posture drift
Compromised layer: none severe. Result: both allow (honest tie).
- id.* clean, net.* clean **[GIVEN]** only device drifts
- dev.agent_present=1, dev.hw_root_trust=1 **[FACT]** agent stays enrolled, hw root physical —
  neither vanishes mid-session
- dev.posture=0.45, dev.patch_level=0.35 **[SWEEP]** mild slip; magnitudes swept

## B_severe — active-compromise drift (EDR flags live malware)
Compromised layer: DEVICE (soft signals only). Result: both allow -> honest LIMITATION.
- id.* clean, net.* clean **[GIVEN]**
- dev.agent_present=1, dev.hw_root_trust=1 **[FACT]** STILL up — malware does not remove the
  enrolled agent or the hardware root mid-session. This is the faithful constraint and the
  whole point: hard-to-forge signals stay clean
- dev.posture=0.05, dev.patch_level=0.2 **[SWEEP]** posture cratered per EDR; magnitudes swept
- device computes to 0.60 (> floor) -> not caught. Reported as limitation (NIST 5.3),
  device=0.60 disclosed as a consequence of the weighting, NOT tuned

## C — supply-chain compromise (agentless edge device)
Compromised layers: DEVICE + NETWORK. Result: coverage gap.
- id.* ~0.85–0.9 **[GIVEN]** identity path itself is not the attack vector
- dev.agent_present=0, dev.hw_root_trust=0 **[FACT]** compromised edge device, unmanaged ([7],[56])
- dev.posture=0.3, dev.patch_level=0.4 **[SWEEP]** swept
- net.eastwest=0.25, net.egress=0.3, net.flow=0.35, net.zone=0.4 **[FACT+SWEEP]** anomalous east-west +
  egress is the network signature of a compromised device ([9] Li, [10] Mishra) — *that these
  drop* is cited; exact levels swept

## D — legacy IIoT / OT lateral movement
Compromised layer: NETWORK. Result: coverage gap (coord ~ tau boundary; floor does the work).
- id.* clean, dev.* clean **[GIVEN]** device + identity look fine; attack is purely lateral
- net.eastwest=0.2 **[FACT]** abnormal east-west is THE lateral-movement signal ([9] Li, [10] Mishra)
- net.zone=0.3, net.egress=0.35, net.flow=0.3 **[SWEEP]** wrong-zone / illegit egress; magnitudes swept

## E — identity compromise (impossible-travel + failed MFA context)
Compromised layer: IDENTITY. Result: both ISOLATE (honest symmetry).
- id.mfa=0 **[FACT]** MFA context fails (NIST Tenet 6) — binary
- id.origin_consistency=0.0 **[FACT]** impossible-travel origin (NIST 3.3.1) — the defining fact
- id.cred_freshness=0.6, id.role_risk_inv=0.7 **[SWEEP]** supporting degradation; swept
- dev.* clean, net.* clean **[GIVEN]** only identity is the vector

## Healthy — baseline control
All signals ~0.95 **[GIVEN]** everything nominal; both allow. Sanity anchor.

---

## What Step 2 (sweep) must cover
Every **[SWEEP]** value above is a magnitude choice. The sweep varies these across plausible
ranges to show the A/C/D gaps and the E symmetry are robust to the exact numbers, and to map
where B_severe would/would not flip. **[FACT]** and **[GIVEN]** values are not swept (they are facts of
the threat, not choices) — except where a sweep of a structural zero tests an edge case on purpose.
