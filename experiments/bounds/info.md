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

 - The constant bounds:
L = {2,3,4}

 - The geometricD bounds:
G = {2,3,4,5}

 - The geometricN bounds (only one type)

 - The data source:
data = {sw, card, sim}

 - For each \( (n,d) \) run 5 times, random sampling \( n \in N \) signatures, constructing lattice from \(d \in D\) shortest, then either doing constant bounds with \(l \in L\) or geometricD bounds with \( g_0 \in G\), or geometricN bounds. Doing SVP with progressive BKZ (betas: 15, 20, 30, 40, 45, 48, 51, 53, 55).

3 * [(3 * 68 * 45) + (4 * 68 * 45) + (1 * 68 * 45)]

```
for data in {sw, card, sim}
    for d in D
        for n in N
        	for l in L
	            schedule one const task with (l, n, d)
	        for g0 in G
	            schedule one geom task with (g0, n, d)
```


### Outputs
Each task outputs {sw,card,sim}\_{geom[2-5],const[2-4]}\_{n}\_{d}.csv with 5 lines for the 5 runs:

`seed, success, duration, last_reduction_step, info, #liars, real_info, bad_info, good_info`

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


---

## During


### Run 25.09. 21:00
 - Some tasks failed to run, due to some CPython error (likely missing Cython?)
 or some weird architecture, or the fact that fpylll was likely compiled with
 march=native or mtune=native?
 - Some tasks had issues due to the use of fish shell to script the task run, when
 run in parallel it needs to lock and access some user specific files, which took
 too much time, sometimes timed out
 - Bad(incomplete) tasks will either not have resulting csv files, or those files will not have 5 lines or those lines will contain the regex "0,.,LLL", collect those and rerun.

### Few reruns

 - First did a rerun of those tasks with "0,.,LLL" which failed due to a C runtime error in G6K native module. Then I actually fixed (recompiled G6K without -march=native) and rerun again.
 - Then also did a rerun for those tasks that were missing the results files, likely due to the above error or some other (ran out of time).

### Few more reruns
 - Got it all.

---

## After

### Figures

### Conclusions

 - Geometric bounds are better than any tested constant bounds, at least on simulated data. This is because they are closer to the real distribution of the bit-length data in D-shortest signatures. They are more aggressive than constant-2 bounds, and so will have more errors, but utilize the information way better. In simulated data, the errors with geom-bounds only arrise due to the random nature of the nonce generation process (e.g. after 4n signatures **around** n signatures will have at least 2 zero msb, this is only true asymptotically).
 - Runtime of the attack is very short, so more exploration into larger lattices or more reduction (higher block sizes) can be performed.
 - There is some interesting behavior happening at dimension 90 with the geom bounds and at dimension around 80 with the const3 bounds, where the success rate suddenly jumps left as well as average block size increases. This might be due to some implementation details of fplll and its BKZ implementation though.