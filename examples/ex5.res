Slope64-py Results
==================
Title: Example 5: A completely submerged homogeneous slope

Geometry:
  w1=30.0  s1=20.0  w2=0.0
  h1=10.0  h2=0.0
  Mesh: 20 x 10 elements

Materials (1 groups):
  Group 1: phi=20.0, c=10.0, psi=0.0, gamma=20.0, E=100000.0, v=0.3

Analysis:
  k_h = 0.0
  gam_w = 9.81
  Iteration limit = 500
  FOS tolerance = 0.02

       SRF    max displ   iterations
---------- ------------ ------------
    0.5000   4.2987e-03            1
    1.0000   1.9536e-01          500
    0.7500   4.6291e-03           25
    0.8750   5.2026e-02          500
    0.8125   9.8762e-03          500
    0.7812   5.0489e-03           47
    0.7969   5.4103e-03           72

Estimated Factor of Safety = 0.80
