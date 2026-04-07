Slope64-py Results
==================
Title: Example 2: A two-layer slope

Geometry:
  w1=1.2  s1=2.0  w2=1.2
  h1=1.0  h2=1.0
  Mesh: 10 x 10 elements

Materials (2 groups):
  Group 1: phi=25.0, c=1.0, psi=0.0, gamma=20.0, E=100000.0, v=0.3
  Group 2: phi=15.0, c=0.5, psi=0.0, gamma=20.0, E=100000.0, v=0.3

Analysis:
  k_h = 0.0
  gam_w = 0.0
  Iteration limit = 500
  FOS tolerance = 0.02

       SRF    max displ   iterations
---------- ------------ ------------
    0.5000   3.0499e-04            1
    1.0000   3.5822e-04           18
    1.5000   6.0144e-03          500
    1.2500   7.2304e-04          500
    1.1250   3.7530e-04           25
    1.1875   3.8497e-04           41
    1.2188   4.3633e-04          337
    1.2344   5.6363e-04          500

Estimated Factor of Safety = 1.23
