# Problem‑Solving Workflow: From Piston–Crank MA to OP Slotted‑Crank → Litvin Noncircular Planetary Mapping

---

## 1) Initial Concept & Objectives

- **Aim:** Formalize *mechanical advantage* (MA) and *transfer efficiency* for a piston driving a rotating member, then generalize to a novel opposed‑piston (OP) engine with planetary “stepper” slots and finally to a Litvin‑style noncircular planetary gearset.
- **Base relation (virtual power):**  \(F_p v_p = \tau\,\omega\).\
  → **Mechanical advantage (rim‑normalized):**
  $$
  \boxed{MA(\theta)=\dfrac{v_p}{\omega r}}\quad (1)
  $$
- **Transmission regimes (qualitative):**\
  • \(v_p<\omega r\Rightarrow MA<1\) (under‑leveraged),\
  • \(v_p=\omega r\Rightarrow MA=1\) (balanced),\
  • \(v_p>\omega r\Rightarrow MA>1\) (torque‑amplified).
- **Transfer efficiency (ideal single‑port):** \(\eta_{tr}=(\tau\omega)/(F_p v_p)=1\) if no auxiliary power ports.

---

## 2) Follow‑Up Questions that Expanded Scope

1. **Force‑transmission scaling:** How do the three velocity‑ratio regimes map to MA and efficiency?\
   → Led to the qualitative table above and power‑based interpretation.
2. **Applied load:** For a vehicle, what is the “ideal” MA? Does it change with load?\
   → Answer: kinematics (MA profile over angle) is fixed by geometry; the *engine‑to‑vehicle match* is via cylinder pressure and transmission gearing.
3. **Novel mechanism:** Introduce a **slotted‑crank OP engine** with controllable planet slots (variable piston acceleration), ring as output, sun for micro‑phasing.\
   → Required multi‑port power mapping with Jacobians.
4. **Gear synthesis:** Map slotted‑crank equations to a **Litvin‑type eccentric, noncircular planetary** using rolling constraints.\
   → Produced conjugate‑gear expressions for MA and efficiency in terms of local pitch radii.

---

## 3) Engine Description A — OP Slotted‑Crank (Generalized Coordinates)

- **Coordinates:** ring angle \(\theta_r\), sun angle \(\theta_s\), slot coordinate \(s\) (kingpin travel from the slot’s origin).
- **Piston law:** \(x_i=x_i(\theta_r,\theta_s,s)\).
- **Jacobian gains:**\
  \(J_{r,i}=\partial x_i/\partial\theta_r\), \(J_{s,i}=\partial x_i/\partial\theta_s\), \(J_{slt,i}=\partial x_i/\partial s\).
- **Velocities:** \(\dot x_i=J_{r,i}\,\omega_r+J_{s,i}\,\omega_s+J_{slt,i}\,\dot s\).
- **Virtual‑power balance (multi‑port):**\
  \(\sum_i F_i\dot x_i=\tau_r\omega_r+\tau_s\omega_s+Q_s\dot s.\)
- **Ring torque (solve from power):**\
  \(\tau_r=\sum_i F_i\Big[J_{r,i}+J_{s,i}\tfrac{\omega_s}{\omega_r}+J_{slt,i}\tfrac{\dot s}{\omega_r}\Big]-\tau_s\tfrac{\omega_s}{\omega_r}-Q_s\tfrac{\dot s}{\omega_r}.\)
- **Mechanical advantage (force‑weighted average over active pistons):**
  $$
  \boxed{MA_r=\langle J_r\rangle+\tfrac{\omega_s}{\omega_r}\langle J_s\rangle+\tfrac{\dot s}{\omega_r}\langle J_{slt}\rangle-\tfrac{\tau_s}{\sum F_i}\tfrac{\omega_s}{\omega_r}-\tfrac{Q_s}{\sum F_i}\tfrac{\dot s}{\omega_r}}\quad (2)
  $$
- **Transfer efficiency (pistons → ring):**
  $$
  \boxed{\eta_{tr}=\dfrac{\tau_r\omega_r}{\sum_i F_i\dot x_i}=1-\dfrac{\tau_s\omega_s+Q_s\dot s}{\sum_i F_i\dot x_i}}\quad (3)
  $$
- **Special modes:**\
  • *Slot & sun locked:* \(MA_r=\langle J_r\rangle\).\
  • *Actuated slot / phasing sun:* extra terms in (2) quantify power exchange with those ports.

---

## 4) Engine Description B — Litvin‑Type Eccentric Noncircular Planetary

- **Local pitch radii vs. roll parameter ****\(\varphi\)****:** \(r_r(\varphi), r_p(\varphi), r_s(\varphi)\).
- **Center‑distance compatibility (internal ring, external sun):**\
  \(\boxed{r_r=r_s+2r_p}\quad (4)\)
- **Rolling without slip at each mesh:**\
  \(r_r\,d\theta_r=r_p\,d\phi\), \(r_s\,d\theta_s=-r_p\,d\phi\)  →\
  \(\boxed{r_r\,d\theta_r+r_s\,d\theta_s=0}\quad (5)\)
- **Piston law via planet roll & slot:** \(x=x(\varphi,s)\), with partials \(x_\varphi\equiv\partial x/\partial\varphi\), \(x_s\equiv\partial x/\partial s\).
- **Jacobian gains (from rolling kinematics):**
  $$
  \boxed{J_r=x_\varphi\,\tfrac{r_r}{r_p}},\qquad
  \boxed{J_s=-x_\varphi\,\tfrac{r_s}{r_p}},\qquad
  \boxed{J_{slt}=x_s}\quad (6)
  $$
- **Piston velocity:**\
  \(\dot x=x_\varphi\Big(\tfrac{r_r}{r_p}\omega_r-\tfrac{r_s}{r_p}\omega_s\Big)+x_s\,\dot s.\)
- **Mechanical advantage (substitute (6) into (2)):**
  $$
  \boxed{MA_r=\Big\langle x_\varphi\Big(\tfrac{r_r}{r_p}-\tfrac{\omega_s}{\omega_r}\tfrac{r_s}{r_p}\Big)\Big\rangle+\tfrac{\dot s}{\omega_r}\langle x_s\rangle-\tfrac{\tau_s}{\sum F_i}\tfrac{\omega_s}{\omega_r}-\tfrac{Q_s}{\sum F_i}\tfrac{\dot s}{\omega_r}}\quad (7)
  $$
- **Transfer efficiency (unchanged form):**\
  \(\boxed{\eta_{tr}=1-\dfrac{\tau_s\omega_s+Q_s\dot s}{\sum_i F_i\dot x_i}}\quad (8)\)
- **Convenient specialization:** If the sun co‑rotates per (5), then \(\omega_s/\omega_r= -\,r_r/r_s\), simplifying (7)’s kinematic part.

---

## 5) Regime Table (Velocity Ratio → Force Leverage)

| Effective piston vs. ring speed | MA behavior | Torque per unit piston force                  |
| ------------------------------- | ----------- | --------------------------------------------- |
| \(v_p<\omega r\)                | \(MA<1\)    | Decreased leverage; higher \(F\) needed       |
| \(v_p=\omega r\)                | \(MA=1\)    | Balanced mapping \(\tau=F r\)                 |
| \(v_p>\omega r\)                | \(MA>1\)    | Amplified leverage; higher \(\tau\) per \(F\) |

*(In the planetary form, “effective” speed is governed by **\(x_\varphi\)** and the local ratios **\(r_r/r_p,\ r_s/r_p\)**, plus any sun/slot actuation.)*

---

## 6) Applications & Control Implications

- **Combustion alignment:** Schedule \(\theta_s(t)\) and \(s(t)\) so \(\langle J_r\rangle + (\omega_s/\omega_r)\langle J_s\rangle + (\dot s/\omega_r)\langle J_{slt}\rangle\) peaks near the crank angle of peak cylinder pressure (≈15–20° ATDC for SI), while minimizing \(Q_s\dot s\).
- **Trade‑offs:** Sun/slot ports can *consume* or *inject* power; (3)/(8) quantify their impact on ring power and efficiency.
- **Design loop:** Pick \(x(\varphi,s)\) → synthesize \(r_p,r_s\) (then \(r_r\) via (4)) → evaluate (6)–(8) over a cycle → iterate to meet pressure‑phasing & stress constraints.

---

## 7) Chronological Workflow Summary (Concise)

1. **Start:** Define MA via velocity ratio (Eq. 1); interpret three regimes.
2. **Load question:** Conclude MA profile is geometric; load affects required cylinder pressure, not kinematics.
3. **OP slotted‑crank model:** Introduce \(\theta_r,\theta_s,s\); derive Jacobians \(J_r,J_s,J_{slt}\), MA (Eq. 2), efficiency (Eq. 3).
4. **Planetary mapping:** Introduce Litvin noncircular planetary with \(r_r,r_p,r_s\), constraints (4)–(5); map Jacobians (Eq. 6); obtain MA (Eq. 7) and efficiency (Eq. 8).

---

## 8) Next Steps (Actionable)

- in its current form, the solver assumes the COM is where the con rod center is placed. This is fine, but it is not optimal for every application. When we think of the simplified model of a crank slider, the system we currently have is akin to example A, we want to work on a platform which acts like example B where the slider is tuned to optimal MA and transfer efficiency at all times. The journal moves axial to the assembly, without much deviation.


- Plug your current geometric generators to compute \(x_\varphi(\varphi,s)\), \(x_s(\varphi,s)\), and \(r_r,r_s,r_p\) along the pairwise contact paths.
- Produce **MA(****\(\theta_r\)****)** and **\(\eta_{tr}(\theta_r)\)** traces for baseline and for candidate \(\theta_s(t), s(t)\) schedules.
- Constrain pressure angle, curvature, and contact ratio in tooth synthesis to maintain feasible Hertzian stresses and avoid undercut/interference.

