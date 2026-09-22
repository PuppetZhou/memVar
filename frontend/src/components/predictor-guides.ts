// Interpretation only. Never use these guide thresholds to generate source calls.
// Reviewed 2026-09-21 against the pinned dbNSFP 5.4a dictionary and official AlphaGenome docs.
export interface PredictorGuide {name:string;meaning:string;scale:string;direction:string;criterion:string;url:string;source:string;}
export const PREDICTOR_GUIDES:Record<string,PredictorGuide> = {
  "Aloft_Fraction_transcripts_affected": {
    "name": "ALoFT fraction",
    "meaning": "Fraction of protein-coding transcripts affected by the variant.",
    "scale": "0–1",
    "direction": "Affected transcript fraction",
    "criterion": "Fraction of affected protein-coding transcripts, not a pathogenicity probability.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Aloft_prob_Dominant": {
    "name": "ALoFT dominant",
    "meaning": "ALoFT probability for the dominant class.",
    "scale": "0–1",
    "direction": "Class probability",
    "criterion": "Read tolerant, recessive and dominant probabilities together with the source ALoFT class; no universal scalar cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Aloft_prob_Recessive": {
    "name": "ALoFT recessive",
    "meaning": "ALoFT probability for the recessive class.",
    "scale": "0–1",
    "direction": "Class probability",
    "criterion": "Read tolerant, recessive and dominant probabilities together with the source ALoFT class; no universal scalar cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Aloft_prob_Tolerant": {
    "name": "ALoFT tolerant",
    "meaning": "ALoFT probability for the tolerant class.",
    "scale": "0–1",
    "direction": "Class probability",
    "criterion": "Read tolerant, recessive and dominant probabilities together with the source ALoFT class; no universal scalar cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "AlphaMissense_score": {
    "name": "AlphaMissense",
    "meaning": "Missense pathogenicity prediction using evolutionary and structural context.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Reference bands: <0.34 likely benign; >0.564 likely pathogenic; otherwise ambiguous. Displayed categories use the matched source call, not a new calculation.",
    "url": "https://www.ensembl.org/info/docs/tools/vep/script/vep_plugins.html#alphamissense",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "BayesDel_addAF_score": {
    "name": "BayesDel +AF",
    "meaning": "Ensemble deleteriousness prediction; addAF and noAF differ in use of population frequency.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "With MaxAF: author-suggested deleterious/tolerated boundary 0.0692655.",
    "url": "https://doi.org/10.1002/humu.23158",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "BayesDel_noAF_score": {
    "name": "BayesDel −AF",
    "meaning": "Ensemble deleteriousness prediction; addAF and noAF differ in use of population frequency.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "Without MaxAF: author-suggested deleterious/tolerated boundary −0.0570105.",
    "url": "https://doi.org/10.1002/humu.23158",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "bStatistic": {
    "name": "bStatistic",
    "meaning": "Expected remaining neutral diversity under background selection, scaled by 1,000.",
    "scale": "0–1,000",
    "direction": "Lower → stronger background selection",
    "criterion": "0 indicates strong loss of neutral diversity; 1,000 indicates little background selection. No clinical cutoff.",
    "url": "https://doi.org/10.1371/journal.pgen.1000471",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "CADD_phred": {
    "name": "CADD PHRED",
    "meaning": "Combined annotations estimate relative variant deleteriousness; raw and PHRED are two representations.",
    "scale": "PHRED rank scale",
    "direction": "Higher → more predicted effect",
    "criterion": "PHRED ranks: 10 ≈ top 10%, 20 ≈ top 1%, 30 ≈ top 0.1%. These are genome-wide ranks, not disease probabilities or universal clinical cutoffs.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "CADD_raw": {
    "name": "CADD raw",
    "meaning": "Combined annotations estimate relative variant deleteriousness; raw and PHRED are two representations.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "ClinPred_score": {
    "name": "ClinPred",
    "meaning": "Ensemble prediction of nonsynonymous variant pathogenicity.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Author-suggested deleterious/tolerated boundary: 0.5.",
    "url": "https://doi.org/10.1016/j.ajhg.2018.08.005",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "DANN_score": {
    "name": "DANN",
    "meaning": "Neural-network functional-effect model using CADD training data.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://doi.org/10.1093/bioinformatics/btu703",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "DEOGEN2_score": {
    "name": "DEOGEN2",
    "meaning": "Missense-effect prediction using molecular, domain, gene and interaction context.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Author-suggested damaging/tolerated boundary: 0.5.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Eigen-PC-phred_coding": {
    "name": "Eigen PC phred",
    "meaning": "Principal-component version of the Eigen integrated annotation score.",
    "scale": "PHRED rank scale",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Eigen-PC-raw_coding": {
    "name": "Eigen PC raw",
    "meaning": "Principal-component version of the Eigen integrated annotation score.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://doi.org/10.1038/ng.3477",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Eigen-phred_coding": {
    "name": "Eigen phred",
    "meaning": "Unsupervised integration of conservation, population frequency and functional-effect annotations.",
    "scale": "PHRED rank scale",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Eigen-raw_coding": {
    "name": "Eigen raw",
    "meaning": "Unsupervised integration of conservation, population frequency and functional-effect annotations.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://doi.org/10.1038/ng.3477",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "ESM1b_score": {
    "name": "ESM1b",
    "meaning": "Protein-language-model log-likelihood ratio for an amino-acid substitution.",
    "scale": "Original score",
    "direction": "Lower → more predicted effect",
    "criterion": "dbNSFP labels reference a −7.5 test-set boundary; the authors do not recommend a universal binary threshold.",
    "url": "https://doi.org/10.1038/s41588-023-01465-0",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "fathmm-XF_coding_score": {
    "name": "FATHMM-XF coding",
    "meaning": "Coding-variant effect prediction using multiple annotation feature groups.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "dbNSFP prediction-field rule: >0.5 damaging; otherwise neutral.",
    "url": "https://doi.org/10.1093/bioinformatics/btx536",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "GERP_92_mammals": {
    "name": "GERP_92_mammals",
    "meaning": "GERP conservation from a 92-mammal alignment.",
    "scale": "Original score",
    "direction": "Higher → greater conservation",
    "criterion": "Conservation evidence, not a clinical classification; no pathogenicity cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "GERP++_NR": {
    "name": "GERP++ NR",
    "meaning": "Evolutionary constraint estimated from substitution rates.",
    "scale": "Original score",
    "direction": "Neutral substitution rate",
    "criterion": "Neutral-rate parameter; do not read it as a pathogenicity or constraint category.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "GERP++_RS": {
    "name": "GERP++ RS",
    "meaning": "Evolutionary constraint estimated from substitution rates.",
    "scale": "Original score",
    "direction": "Higher → greater conservation",
    "criterion": "Conservation evidence, not a clinical classification; no pathogenicity cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "gMVP_score": {
    "name": "gMVP",
    "meaning": "Graph-attention model for missense pathogenicity prediction.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "GPN_MSA_score": {
    "name": "GPN-MSA",
    "meaning": "DNA-language-model prediction using multispecies sequence alignments.",
    "scale": "Original score",
    "direction": "Lower → more predicted effect",
    "criterion": "dbNSFP prediction-field rule: <−7 damaging; otherwise tolerated.",
    "url": "https://doi.org/10.1038/s41587-024-02511-w",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "LIST-S2_score": {
    "name": "LIST-S2",
    "meaning": "Sequence-based prediction of nonsynonymous variant effects.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Author-suggested deleterious/tolerated boundary: 0.85.",
    "url": "https://doi.org/10.1093/nar/gkaa288",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "M-CAP_score": {
    "name": "M-CAP",
    "meaning": "Ensemble model for prioritizing potentially damaging missense variants.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Source damaging/tolerated boundary: 0.025; higher scores favor damaging.",
    "url": "https://doi.org/10.1038/ng.3703",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MetaLR_score": {
    "name": "MetaLR",
    "meaning": "Logistic-regression ensemble combining prediction, conservation and population-frequency features.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Source damaging/tolerated boundary: 0.5; higher scores favor damaging.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MetaRNN_score": {
    "name": "MetaRNN",
    "meaning": "Recurrent-neural-network ensemble combining prediction scores, conservation and allele frequencies.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Source damaging/tolerated boundary: 0.5; higher scores favor damaging.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MetaSVM_score": {
    "name": "MetaSVM",
    "meaning": "Support-vector ensemble combining prediction, conservation and population-frequency features.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "Source damaging/tolerated boundary: 0; higher scores favor damaging.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MisFit_D_score": {
    "name": "MisFit D",
    "meaning": "Missense effects on protein function and evolutionary selection.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Author suggestions for disease genes: 0.45 (lenient) to 0.55 (stringent). No single cutoff is applied here.",
    "url": "https://doi.org/10.1038/s41467-025-59937-2",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MisFit_S_score": {
    "name": "MisFit S",
    "meaning": "Missense effects on protein function and evolutionary selection.",
    "scale": "0–0.5",
    "direction": "Higher → stronger negative selection",
    "criterion": "No fixed pathogenicity cutoff is recommended. Values <10⁻⁴ are considered noise; interpretation depends on gene and age of onset.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MPC_score": {
    "name": "MPC",
    "meaning": "Missense impact using regional missense constraint.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://doi.org/10.1101/148353",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MutationAssessor_score": {
    "name": "MutationAssessor",
    "meaning": "Functional impact based on conservation within protein families and subfamilies.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "Source impact boundaries: 0.8 (neutral/low), 1.935 (low/medium), 3.5 (medium/high). These are functional-impact categories.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MutationTaster_score": {
    "name": "MutationTaster2021",
    "meaning": "Disease-potential annotation; interpret the score together with its source prediction and model.",
    "scale": "0–1",
    "direction": "Read together with the source call",
    "criterion": "The dictionary mixes legacy score conventions with 2021 annotations. Read the matched A/D/N/P source call; do not derive a new category from this score.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MutFormer_score": {
    "name": "MutFormer",
    "meaning": "Protein-context transformer model for missense effects.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Suggested boundary 0.8838, recorded by dbNSFP as author personal communication.",
    "url": "https://doi.org/10.1016/j.xinn.2023.100487",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MutPred2_score": {
    "name": "MutPred2",
    "meaning": "Amino-acid substitution impact with potential molecular mechanisms.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "dbNSFP calibrated calls: BS ≤0.010; BM (0.010,0.197]; BP (0.197,0.391]; UC (0.391,0.737); PP [0.737,0.829); PM [0.829,0.932); PS ≥0.932. These are source computational-evidence bands, not a combined clinical assessment.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MutScore_score": {
    "name": "MutScore",
    "meaning": "Ensemble substitution predictor incorporating positional clustering.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Suggested boundary 0.5, recorded by dbNSFP as author personal communication.",
    "url": "https://doi.org/10.1016/j.ajhg.2022.01.006",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "MVP_score": {
    "name": "MVP",
    "meaning": "Deep-learning model for missense pathogenicity prediction.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Author suggestions reported by dbNSFP: 0.7 for genes with ExAC pLI ≥0.5, 0.75 for pLI <0.5. Do not apply either without gene context.",
    "url": "https://doi.org/10.1101/259390",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "PHACTboost_score": {
    "name": "PHACTboost",
    "meaning": "Gradient-boosted prediction using alignments, phylogeny and ancestral reconstruction.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Suggested boundary 0.62, recorded by dbNSFP as author personal communication.",
    "url": "https://doi.org/10.1093/molbev/msae136",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "phastCons100way_vertebrate": {
    "name": "phastCons 100",
    "meaning": "Probability that a site belongs to a conserved element. Alignment: vertebrate, 100 genomes.",
    "scale": "0–1",
    "direction": "Higher → greater conservation",
    "criterion": "Conservation evidence, not a clinical classification; no pathogenicity cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "phastCons17way_primate": {
    "name": "phastCons 17",
    "meaning": "Probability that a site belongs to a conserved element. Alignment: primate, 17 genomes.",
    "scale": "0–1",
    "direction": "Higher → greater conservation",
    "criterion": "Conservation evidence, not a clinical classification; no pathogenicity cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "phastCons470way_mammalian": {
    "name": "phastCons 470",
    "meaning": "Probability that a site belongs to a conserved element. Alignment: mammalian, 470 genomes.",
    "scale": "0–1",
    "direction": "Higher → greater conservation",
    "criterion": "Conservation evidence, not a clinical classification; no pathogenicity cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "phyloP100way_vertebrate": {
    "name": "phyloP 100",
    "meaning": "Site conservation or accelerated evolution relative to a neutral model. Alignment: vertebrate, 100 genomes.",
    "scale": "0–1",
    "direction": "Higher → greater conservation",
    "criterion": "Conservation evidence, not a clinical classification; no pathogenicity cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "phyloP17way_primate": {
    "name": "phyloP 17",
    "meaning": "Site conservation or accelerated evolution relative to a neutral model. Alignment: primate, 17 genomes.",
    "scale": "Original score",
    "direction": "Higher → greater conservation",
    "criterion": "Conservation evidence, not a clinical classification; no pathogenicity cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "phyloP470way_mammalian": {
    "name": "phyloP 470",
    "meaning": "Site conservation or accelerated evolution relative to a neutral model. Alignment: mammalian, 470 genomes.",
    "scale": "0–1",
    "direction": "Higher → greater conservation",
    "criterion": "Conservation evidence, not a clinical classification; no pathogenicity cutoff.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Polyphen2_HDIV_score": {
    "name": "PolyPhen-2 HDIV",
    "meaning": "Protein substitution effects using sequence and structural features; HumDiv model.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Source D/P/B bins: D 0.957–1; P 0.454–0.956; B 0–0.452. The rounded dictionary has gaps: retain the supplied call, do not re-bin boundary values.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "Polyphen2_HVAR_score": {
    "name": "PolyPhen-2 HVAR",
    "meaning": "Protein substitution effects using sequence and structural features; HumVar model.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Source D/P/B bins: D 0.909–1; P 0.447–0.908; B 0–0.446. Retain the supplied call at boundaries.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "popEVE_score": {
    "name": "popEVE",
    "meaning": "Variant severity model combining cross-species and human population variation.",
    "scale": "Original score",
    "direction": "Lower → more predicted effect",
    "criterion": "Source bands: <−5.056 severe; [−5.056,−4.617) moderate; ≥−4.617 benign. These are model labels, not ClinVar assertions.",
    "url": "https://doi.org/10.1038/s41588-025-02400-1",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "PrimateAI_score": {
    "name": "PrimateAI",
    "meaning": "Neural-network missense predictor informed by variation in nonhuman primates.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "Author-suggested damaging/tolerated boundary: 0.803.",
    "url": "https://doi.org/10.1038/s41588-018-0167-z",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "PROVEAN_score": {
    "name": "PROVEAN",
    "meaning": "Functional effects of protein changes estimated from sequence similarity.",
    "scale": "Original score",
    "direction": "Lower → more predicted effect",
    "criterion": "Source rule: ≤−2.5 damaging; otherwise neutral.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "REVEL_score": {
    "name": "REVEL",
    "meaning": "Ensemble missense predictor combining multiple functional-effect scores.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "SIFT4G_score": {
    "name": "SIFT4G",
    "meaning": "Genome-scale SIFT substitution-tolerance predictions.",
    "scale": "0–1",
    "direction": "Lower → more predicted effect",
    "criterion": "dbNSFP 5.4a source rule: <0.05 damaging; otherwise tolerated.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "SIFT_score": {
    "name": "SIFT",
    "meaning": "Amino-acid substitution tolerance from homologous protein sequences.",
    "scale": "0–1",
    "direction": "Lower → more predicted effect",
    "criterion": "dbNSFP 5.4a source rule: <0.05 damaging; otherwise tolerated.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "VARITY_ER_LOO_score": {
    "name": "VARITY ER LOO",
    "meaning": "Missense pathogenicity models for rare (R) or extremely rare (ER) variants; LOO changes training-variant evaluation. Leave-one-variant-out predictions for training variants.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://doi.org/10.1016/j.ajhg.2021.08.012",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "VARITY_ER_score": {
    "name": "VARITY ER",
    "meaning": "Missense pathogenicity models for rare (R) or extremely rare (ER) variants; LOO changes training-variant evaluation. Standard model output.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://doi.org/10.1016/j.ajhg.2021.08.012",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "VARITY_R_LOO_score": {
    "name": "VARITY R LOO",
    "meaning": "Missense pathogenicity models for rare (R) or extremely rare (ER) variants; LOO changes training-variant evaluation. Leave-one-variant-out predictions for training variants.",
    "scale": "Original score",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://doi.org/10.1016/j.ajhg.2021.08.012",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "VARITY_R_score": {
    "name": "VARITY R",
    "meaning": "Missense pathogenicity models for rare (R) or extremely rare (ER) variants; LOO changes training-variant evaluation. Standard model output.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://doi.org/10.1016/j.ajhg.2021.08.012",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "VEST4_score": {
    "name": "VEST4",
    "meaning": "Missense functional-effect prediction from the VEST 4.0 classifier.",
    "scale": "0–1",
    "direction": "Higher → more predicted effect",
    "criterion": "No binary cutoff is supplied for this field in the reviewed dbNSFP dictionary. Read the original score and method context.",
    "url": "https://www.dbnsfp.org/releases/",
    "source": "dbNSFP 5.4a field dictionary"
  },
  "alphagenome_avi_raw": {
    "name": "AVI raw",
    "meaning": "Atlas integrated variant-impact ranking; raw and PHRED describe the same model.",
    "scale": "Raw model score",
    "direction": "Higher → more predicted impact",
    "criterion": "No clinical cutoff applied. AVI overlaps other evidence, including AlphaMissense and splicing; do not count them as independent votes.",
    "url": "https://deepmind.google/blog/alphagenome-atlas-a-predictive-map-of-every-possible-dna-letter-change-in-the-human-genome/",
    "source": "AlphaGenome Atlas · published source scores"
  },
  "alphagenome_avi_phred": {
    "name": "AVI PHRED",
    "meaning": "Atlas integrated variant-impact ranking; raw and PHRED describe the same model.",
    "scale": "PHRED rank scale",
    "direction": "Higher → more predicted impact",
    "criterion": "No clinical cutoff applied. AVI overlaps other evidence, including AlphaMissense and splicing; do not count them as independent votes. PHRED 10/20/30 ≈ top 10%/1%/0.1%, not disease probabilities.",
    "url": "https://deepmind.google/blog/alphagenome-atlas-a-predictive-map-of-every-possible-dna-letter-change-in-the-human-genome/",
    "source": "AlphaGenome Atlas · published source scores"
  },
  "alphagenome_splicing": {
    "name": "AlphaGenome splicing",
    "meaning": "Combined magnitude of splice-site, splice-usage and splice-junction changes.",
    "scale": "Merged source score",
    "direction": "Higher → more predicted impact",
    "criterion": "No binary cutoff applied. Merged magnitude is not PSI, a tissue-specific effect or a signed splicing change.",
    "url": "https://www.alphagenomedocs.com/faqs.html",
    "source": "AlphaGenome Atlas · published source scores"
  }
};

// Author-maintained sites/repositories checked 2026-09-22.
// Keep these separate from field dictionaries and method publications.
export interface PredictorProject { url:string; label:string; }
const PREDICTOR_PROJECTS:Record<string,PredictorProject> = {
  Aloft:{url:'https://github.com/gersteinlab/aloft',label:'Official repository'},
  AlphaMissense:{url:'https://github.com/google-deepmind/alphamissense',label:'Official repository'},
  CADD:{url:'https://cadd.gs.washington.edu/',label:'Tool website'},
  REVEL:{url:'https://sites.google.com/site/revelgenomics/',label:'Tool website'},
  SIFT:{url:'https://sift.bii.a-star.edu.sg/',label:'Tool website'},
  SIFT4G:{url:'https://sift.bii.a-star.edu.sg/sift4g/',label:'Tool website'},
  ESM1b:{url:'https://github.com/ntranoslab/esm-variants',label:'Official repository'},
  GPN:{url:'https://github.com/songlab-cal/gpn',label:'Official repository'},
  alphagenome:{url:'https://www.alphagenomedocs.com/',label:'Official documentation'},
};
export function predictorProject(field:string):PredictorProject|undefined {
  return PREDICTOR_PROJECTS[field.split('_')[0]];
}
