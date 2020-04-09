# Experiment 3 - Recentering

---

### Hypothesis
Recentering is better, even if strictly speaking the inequalities are not always true (just most of the time).

### Setup

 - The dimensions:
D = {50, 52, ..., 140}

 - The number of signatures used:
N = {500, 600, ..., 7000, 8000, 9000, 10000}

 - The data source:
data = {sim, sw, card, tpm}

 - The recentering used:
rec = {yes, no}

 - each run 5 times, random sampling \( n \in N \) signatures, constructing lattice from \(d \in D\) shortest signatures, doing the selected bounds. Doing SVP with progressive BKZ (betas: 15, 20, 30, 40, 45, 48, 51, 53, 55).

 - In this experiment, we use \( l_i+1 \) instead of \( l_i \) in the matrix if we are in the recentering cases.  Furthermore, the values \( 2^{l_i+1}u_i \) are replaced with \( 2^{l_i+1}u_i + n \) if recentering is used.

### Outputs
Each task outputs {sw,card,sim,tpm}\_{geomN,geom[1-4],known}\_{n}\_{d}.csv with 5 lines for the 5 runs:

`seed, success, duration, last_reduction_step, info, #liars, real_info, bad_info, good_info, liar_positions, result_normdist, result_row`

### Visualizations

 - 3D plot, x:N, y:D, z: number of successes
 - 3D plot, x:N, y:D, z: last reduction step
 - 3D plot, x:N, y:D, z: avg. duration of successful run
 - 2D lineplot, x:N, y: avg. of success over d in D
 - etc.

### Why?

 - Compares both centering possibilities to the baseline.

### Conclusions

 - Recentering works better than no recentering.
 - Recentering behaves weirdly on geom2 bounds.