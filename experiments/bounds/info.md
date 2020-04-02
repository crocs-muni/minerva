# Experiment 1 -  Geometric vs constant bounds

---

## Before

### Hypothesis
Geometric bounds are better. If the Brumley&Tuveri method is used, even in the presence of noise.

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
 data = {sw, card, sim, tpm}

 - For each \( (n,d) \) run 5 times, random sampling \( n \in N \) signatures,
 constructing lattice from \(d \in D\) shortest, then either doing constant
 bounds with \(l \in L\) or geometricD bounds with \( g_0 \in G\), or geometricN bounds.
 Doing SVP with progressive BKZ (betas: 15, 20, 30, 40, 45, 48, 51, 53, 55).

### Outputs
Each task outputs {sw,card,sim,tpm}\_{geom[1-4],const[1-4],geomN,known,knownre,template[01,10,30]}\_{n}\_{d}.csv with 5 lines for the 5 runs:

`seed, success, duration, last_reduction_step, info, #liars, real_info, bad_info, good_info[,liar_positions,result_normdist,result_row]`

### Visualizations
For both real and sim data:

 - 3D plot, x:N, y:D, z: number of successes; this for geom,const2,const3,const4.
 - 3D plot, x:N, y:D, z: last reduction step; this for geom,const2,const3,const4.
 - 3D plot, x:N, y:D, z: avg. duration of successful run; this for geom,const2,const3,const4.
 - 2D lineplot, x:N, y:sum over d in D (number of successed); all of geom,const2,const3,const4 in one plot.

### Why?
 - Gives a lot of insight into the parameter space.
 - Gives a good baseline for future experiments, can compare in different parts of the parameter space.
 - Shows superiority of out parameter choice of geometric distribution.

### Conclusions

 - Geometric bounds are better than any tested constant bounds, at least on simulated data. This is because they are closer to the real distribution of the bit-length data in D-shortest signatures. They are more aggressive than constant-2 bounds, and so will have more errors, but utilize the information way better. In simulated data, the errors with geom-bounds only arrise due to the random nature of the nonce generation process (e.g. after 4n signatures **around** n signatures will have at least 2 zero msb, this is only true asymptotically).
 - Runtime of the attack is very short, so more exploration into larger lattices or more reduction (higher block sizes) can be performed.
 - There is some interesting behavior happening at dimension 90 with the geom bounds and at dimension around 80 with the const3 bounds, where the success rate suddenly jumps left as well as average block size increases. This might be due to some implementation details of fplll and its BKZ implementation though.