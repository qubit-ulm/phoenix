"""Demo scripts split into two independent staged series.

Series ``01x``:
   executable spin-dynamics demos that start with a hand-written generator,
   apply it to a trajectory, and then extend the model with higher-order
   correction terms.

Series ``02x``:
   symbolic-model construction demos that move from keymaps to explicit local
   cases and then to ``MapApplyInstruction`` on a lattice.

Series ``03x``:
   side-by-side backend generation previews for one shared symbolic routine.

Series ``04x``:
   explicit buffer placement, serial/OpenMP source comparisons, and a runtime
   benchmark with several fixed thread counts.

Series ``05x``:
   atomic-region lowering previews for different attachment modes.

Series ``06x``:
   user-facing configuration and backend smoke-test walkthroughs.

Series ``07x``:
   ADAA family comparisons with host/device transfer notes.

Series ``08x``:
   generated library packaging and shared makefile layout.
"""
