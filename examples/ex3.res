Slope64-py Results
==================
Title: Example 3: A two-layer undrained clay slope

Geometry:
  w1=20.0  s1=20.0  w2=20.0
  h1=10.0  h2=10.0
  Mesh: 30 x 10 elements

Materials (2 groups):
  Group 1: phi=0.0, c=50.0, psi=0.0, gamma=20.0, E=100000.0, v=0.3
  Group 2: phi=0.0, c=73.1, psi=0.0, gamma=20.0, E=100000.0, v=0.3

Analysis:
  k_h = 0.0
  gam_w = 0.0
  Iteration limit = 500
  FOS tolerance = 0.02

       SRF    max displ   iterations
---------- ------------ ------------
    0.5000   3.0436e-02            1
    1.0000   3.4126e-02            4
    1.5000   4.3280e-02           33
    2.0000   6.9963e-02          500
    1.7500   5.0299e-02           62
    1.8750   5.4100e-02           74
    1.9375   5.6600e-02           94
    1.9688   5.8409e-02          124
    1.9844   5.9891e-02          162

Estimated Factor of Safety = 1.99
