> Repository packaging: PDFs are excluded by the existing release rule. The two SVGs larger than 5 MB (`main/Fig2_bland_altman.svg` and `supplementary/FigS3_signal_verification.svg`) remain in the source ZIP/local review folder; regenerate them from the figure scripts. Other SVGs are included. The descriptions below refer to the authors' source package.

# Vector figures (Head IMU cadence, IEEE Sensors J. submission)

Each figure is given as PDF (vector, fonts embedded) and SVG (converted from the PDF; text as outlines).
Numbering follows the built manuscript and supplement (2026-10-28).

| File | In the paper | Source in the build |
|---|---|---|
| main/Fig1_sensors_mounting | Fig. 1 Sensors and mounting errors | fig_schematics (build_fig1b.py; SVG is the editable original) |
| main/Fig2_bland_altman | Fig. 2 Bland–Altman plots (B0) | fig_results/fig5_bland_altman (re-exported without rasterized scatter layers; PNG identical) |
| main/Fig3_head_only_end_to_end | Fig. 3 Head-only end-to-end estimation | fig_v16/fig10_endtoend |
| main/Fig4_mounting_simulations | Fig. 4 Mounting simulations | fig_results/fig7_simulations |
| main/Fig5_trustworthiness | Fig. 5 Trustworthiness | fig_v16/fig11_trust |
| supplementary/FigS1_pipeline | Fig. S1 Processing and evaluation pipeline (B0) | fig_ieee/fig2_method_flowchart |
| supplementary/FigS2_inclusion_split | Fig. S2 Trial inclusion and split | fig_results/fig3_inclusion_flow |
| supplementary/FigS3_signal_verification | Fig. S3 Signal-level verification | fig_results/figS1_signal_qc |
| supplementary/FigS4_example_trial | Fig. S4 Example trial PD_15_2 | fig_results/fig4_example_trial |
| supplementary/FigS5_error_by_cohort | Fig. S5 B0 error by cohort | fig_results/fig6_cohorts |
| supplementary/FigS6_cross_visit | Fig. S6 Cross-visit agreement | fig_results/fig8_rewear |
| supplementary/FigS7_turn_gate_random | Fig. S7 Turn gate vs random removal | fig_results/fig9_gating |
| supplementary/FigS8_external_bland_altman | Fig. S8 DUO-GAIT Bland–Altman | fig_v16/figS_external_ba |
| graphical_abstract/GA_first_page_compact | Image beside the abstract (first page) | svgrev/build_ga2.py (SVG editable) |
| graphical_abstract/GA_full_design | Authors' full graphical abstract (revised) | svgrev/build.py (SVG editable) |

The walker in Fig. 1 and both graphical abstracts is a traced vector illustration (paths), not a raster image.
Fig2 and FigS3 SVGs are large (≈6–7 MB) because every data point is a separate vector shape; use the PDF in
Illustrator/Inkscape if the SVG is slow.
