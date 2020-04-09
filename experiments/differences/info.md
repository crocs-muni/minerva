# Experiment 4 - Differences

---

### Hypothesis
One of the approaches via differences might reduce either the time or the number of signatures needed.

### Setup

 - The dimensions:
   D = {50, 52, ..., 140}

 - The number of signatures used:
   N = {500, 600, ..., 7000, 8000, 9000, 10000}

 - The data source:
   data = {sim, sw, card, tpm}

 - The differences:
  diffs = {diff, nodiff}
  
 - each run 5 times, random sampling \( n \in N \) signatures, constructing lattice from \(d+1 \in D\) shortest. The lattice is constructed from differences of neighboring signatures, taking the minimum of their bounds as the bound for the resulting inequality. Doing SVP with progressive BKZ.

 - Recentering is not used.

### Outputs
Each task outputs {sim,sw,card,tpm}\_{geomN}\_{diff,nodiff}\_{n}\_{d}.csv with 5 lines for the 5 runs:

`seed, success, duration, last_reduction_step, info, #liars, real_info, bad_info, good_info, liar_positions, result_normdist, result_row`

The output info, liars, etc. is computed from the differences that are used in
the lattice, not from the source signatures.

### Visualizations

 - 3D plot, x:N, y:D, z: number of successes
 - 3D plot, x:N, y:D, z: last reduction step
 - 3D plot, x:N, y:D, z: avg. duration of successful run
 - 2D lineplot, x:N, y: avg. of success over d in D
 - etc.

### Why?
 - Compares how differences fare against the baseline.

### Conclusions
 - Taking the differences is better than baseline, it is almost
 as good as using recentering (which cannot be used with recentering).
