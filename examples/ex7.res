Slope64-py Results
==================
Title: Example 7: A two-layer slope subjected to a horizontal pseudo-acceleration

Geometry:
  w1=30.0  s1=20.0  w2=30.0
  h1=10.0  h2=10.0
  Mesh: 80 x 20 elements

Materials (1 groups):
  Group 1: phi=30.0, c=20.0, psi=0.0, gamma=20.0, E=100000.0, v=0.3

Analysis:
  k_h = 0.25
  gam_w = 9.81
  Iteration limit = 2000
  FOS tolerance = 0.02

       SRF    max displ   iterations
---------- ------------ ------------
    0.5000   4.6686e-02           19
    1.0000   5.1723e-02           14
    1.5000   6.7531e-01         2000
    1.2500   5.9877e-02          260
    1.3750   6.6873e-02          408
    1.4375   2.5572e-01         2000
    1.4062   1.1838e-01         2000
    1.3906   6.7832e-02         2000

Estimated Factor of Safety = 1.38
