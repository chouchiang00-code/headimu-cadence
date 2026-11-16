Build: put results_v16 next to ieee/ (or set V16_RESULTS), then
  cd ieee
  python build_jsen.py main Head_IMU_V16_IEEE_Sensors_J_manuscript.docx   (add --bios for biography placeholders)
  python build_jsen.py supp Head_IMU_V16_Supplementary_Material.docx
(build_jsen.py = IEEE Sensors Journal colorized template; build_ieee.py = previous plain IEEE layout)
Figures referenced by the documents are included under fig_*/.

Paper title: Cadence From a Single Forehead IMU in Clinical Cohorts: Comparison With the Lower Back
See ../README.md for current setup, the new root-level builders, and known result/asset prerequisites.
Versioned drafts and the ieee/ folder are retained as reference build sources. Only title/running-head metadata was synchronized; older scientific content is not the final submission.
