# Experiment 1 -  Geometric vs constant bounds

---

### Hypothesis
Geometric bounds are better. Geometric N bounds are the best. If the basic method is used, even in the presence of noise.

### Setup

 - The dimensions:
 D = {50, 52, ..., 140}

 - The number of signatures used:
 N = {500, 600, ..., 7000, 8000, 9000, 10000}

 - The bounds type:
    * The constant bounds:
    L = {1,2,3,4}

    * The geometricD bounds:
    G = {1,2,3,4}

    * The geometricN bounds (only one type)

    * The known bounds (with or without recentering)

    * The templated bounds (with \(\alpha \in \{0.01, 0.1, 0.3\} = A\))

 - The data source:
 data = {sim, sw, card, tpm}

 - For each \( (n,d) \) run 5 times, random sampling \( n \in N \) signatures,
 constructing lattice from \(d \in D\) shortest, then either doing constant
 bounds with \(l \in L\) or geometricD bounds with \( g_0 \in G\), or geometricN bounds.
 Doing SVP with progressive BKZ (betas: 15, 20, 30, 40, 45, 48, 51, 53, 55).

### Outputs
Each task outputs {sw,card,sim,tpm}\_{geom[1-4],const[1-4],geomN,known,knownre,template[01,10,30]}\_{n}\_{d}.csv with 5 lines for the 5 runs:

`seed, success, duration, last_reduction_step, info, #liars, real_info, bad_info, good_info, liar_positions, result_normdist, result_row`

### Visualizations

 - 3D plot, x:N, y:D, z: number of successes
 - 3D plot, x:N, y:D, z: last reduction step
 - 3D plot, x:N, y:D, z: avg. duration of successful run
 - 2D lineplot, x:N, y: avg. of success over d in D
 - etc.

### Why?
 - Gives a lot of insight into the parameter space.
 - Gives a good baseline for future experiments, can compare in different parts of the parameter space.
 - Shows superiority of out parameter choice of geometric distribution.

### Conclusions

 - GeometricD bounds are better than any tested constant bounds.
 - GeometricN bounds are the best
 - Runtime of the attack is very short, so more exploration into larger lattices or more reduction (higher block sizes) can be performed.
 - There is some interesting behavior happening at dimension 90 with the geometricD bounds and at dimension around 80 with the const3 bounds, where the success rate suddenly jumps left as well as average block size increases. This might be due to some implementation details of fplll and its BKZ implementation though.