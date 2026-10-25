Build: put results_v16 next to ieee/ (or set V16_RESULTS), then
  cd ieee
  python build_jsen.py main Head_IMU_V16_IEEE_Sensors_J_manuscript.docx --bios
  python build_jsen.py supp Head_IMU_V16_Supplementary_Material.docx
(build_jsen.py = IEEE Sensors Journal colorized template; build_ieee.py = previous plain IEEE layout)
Figures referenced by the documents are included under fig_*/.
