# Experiment 5 -  Random subsets (broken)

---

## Before

### Hypothesis

Taking random subsets of a reasonably sized set of signatures might reduce the number of liars and increase the probability of success.

### Setup

 - The dimensions:
   D = {50, 52, ..., 140}

 - The number of signatures used:
   N = {500, 600, ..., 7000, 8000, 9000, 10000}

 - The data source:
   data = {sim, sw, card, tpm}

 - The oversampling factor:
   C = {1, 1.5}
   where c = 1 means no random subsets.

 - randomly selected \(d\) signatures from the shortest \( min(c*d, N) \) signatures are used, this is repeated upto 200.

 - each run 5 times, constructing lattice, then doing SVP with progressive BKZ.


### Outputs
Each task outputs {sw,card,sim,tpm}\_{geomN}\_{svp}\_{yes}\_{c}\_{n}\_{d}.csv with 5 lines for the 5 runs:

`seed, success, duration, last_reduction_step, info, #liars, real_info, bad_info, good_info, liar_positions, result_normdist, result_row`

### Visualizations

 - 3D plot, x:N, y:D, z: number of successes
 - 3D plot, x:N, y:D, z: last reduction step
 - 3D plot, x:N, y:D, z: avg. duration of successful run
 - 2D lineplot, x:N, y: avg. of success over d in D
 - etc.
 
### Why?
 - We need to compare our method to the random subsets method.

### Conclusions
 - This approach errorneously did not work. As in, the attack and success rate
 of doing this does not represent what the random subsets method calls for.
 To properly test random subsets, we need one attack to represent many attacks
 with sampling different \( d \) signatures out of \( c * d \) of the shortest.
 To measure success rate, we need to do this over the randomness of the pick of N
 signatures. This will be done in a separate experiment.
