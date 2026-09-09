// Génère docs/hypotheses_a_priori_cross_domaine.docx : node scripts/build_hypotheses_docx.js docs/hypotheses_a_priori_cross_domaine.docx  (npm install docx)
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType,
  AlignmentType, LevelFormat, BorderStyle, ShadingType, TableOfContents, PageBreak, Footer, PageNumber, Header
} = require("docx");

const FONT = "Calibri";
const P = (text, opts = {}) => new Paragraph({ spacing: { after: 120 }, ...opts, children: Array.isArray(text) ? text : [new TextRun({ text, font: FONT, size: 22, ...(opts.run || {}) })] });
const R = (text, o = {}) => new TextRun({ text, font: FONT, size: 22, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, children: [new TextRun({ text: t, font: FONT })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 }, children: [new TextRun({ text: t, font: FONT })] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 200, after: 100 }, children: [new TextRun({ text: t, font: FONT })] });
const B = (runs, level = 0) => new Paragraph({ numbering: { reference: "bullets", level }, spacing: { after: 60 }, children: (typeof runs === "string" ? [R(runs)] : runs) });
const N = (runs) => new Paragraph({ numbering: { reference: "nums", level: 0 }, spacing: { after: 60 }, children: (typeof runs === "string" ? [R(runs)] : runs) });
const cite = (n) => R(` [${n}]`, { superScript: false, color: "1F4E79" });

function table(header, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, w, isH = false) => new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: isH ? { fill: "DCE6F1", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 80, right: 80 },
    children: [new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text: t, font: FONT, size: 18, bold: isH })] })],
  });
  return new Table({
    width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, widths[i], true)) }),
      ...rows.map(r => new TableRow({ children: r.map((c, i) => cell(String(c), widths[i])) }))],
  });
}
const gap = () => new Paragraph({ spacing: { after: 120 }, children: [] });

// ---------------------------------------------------------------- références
const refs = [
  "Zhao Y., Lv W., Xu S. et al. (2024). DETRs Beat YOLOs on Real-time Object Detection. CVPR 2024. https://openaccess.thecvf.com/content/CVPR2024/html/Zhao_DETRs_Beat_YOLOs_on_Real-time_Object_Detection_CVPR_2024_paper.html — RT-DETR-R50 : AP 53,1 ; AP_S 34,8 / AP_M 58,2 / AP_L 71,0 (COCO val2017).",
  "Lv W., Zhao Y., Chang Q. et al. (2024). RT-DETRv2: Improved Baseline with Bag-of-Freebies for Real-Time Detection Transformer. arXiv:2407.17140. — gains de +1,0 à +1,4 AP sur RT-DETR à taille égale.",
  "Akyon F.C., Altinuc S.O., Temizel A. (2022). Slicing Aided Hyper Inference and Fine-tuning for Small Object Detection. IEEE ICIP 2022. arXiv:2202.06934. — VisDrone/xView : +6,8 / +5,1 / +5,3 AP (FCOS, VFNet, TOOD) par tuilage à l'inférence ; +12,7 / +13,4 / +14,5 AP avec fine-tuning tuilé.",
  "Wang J., Xu C., Yang W., Yu L. (2021). A Normalized Gaussian Wasserstein Distance for Tiny Object Detection. arXiv:2110.13389 ; Xu C. et al. (2022) Detecting tiny objects in aerial images: a normalized Wasserstein distance and a new benchmark, ISPRS J. Photogramm. Remote Sens. — objet 6×6 px : une déviation mineure fait chuter l'IoU de 0,53 à 0,06 ; +6,7 AP sur AI-TOD ; RFLA 24,8 AP sur AI-TOD.",
  "Wu Z., Hall S.B., Kimber A.J. et al. (2022). Automated aerial animal detection when spatial resolution conditions are varied. Computers and Electronics in Agriculture 193, 106689. arXiv:2110.01329. — chute brutale des performances autour d'une GSD de 0,5 m/px ; mAP −52 % avec ouverture Cassegrain à 0,5 m/px.",
  "Borowicz A., Le H., Humphries G. et al. (2019). Aerial-trained deep learning networks for surveying cetaceans from satellite imagery. PLOS ONE 14(10): e0212532. — CNN entraînés sur imagerie aérienne sous-échantillonnée, testés sur WorldView-3 (31 cm) : 100 % des tuiles avec baleine et 94 % des tuiles d'eau correctement classées ; F1 = 0,968.",
  "Guirado E., Tabik S., Rivas M.L., Alcaraz-Segura D., Herrera F. (2019). Whale counting in satellite and aerial images with deep learning. Scientific Reports 9, 14259. — F1 = 0,81 en détection (présence) et 0,94 en comptage.",
  "Green K.M., Virdee M.K., Cubaynes H.C. et al. (2023). Gray whale detection in satellite imagery using deep learning. Remote Sensing in Ecology and Conservation 9(6), 829-840. doi:10.1002/rse2.352. — YOLOv5, apprentissage combiné drone (53 baleines, Oregon) + satellite ; 344/69/90 baleines en train/val/test.",
  "Zheng Y., Yang J., Chen Y. et al. (2025). Beluga Whale Detection from Satellite Imagery with Point Labels. IGARSS 2025. arXiv:2505.12066. — YOLOv8 sur boîtes SAM : F1 72,2 % (bélugas), 70,3 % (phoques du Groenland) ; boîtes SAM > boîtes tampon.",
  "Kapoor S., Kumar M., Kaushal M. (2023). Deep learning based whale detection from satellite imagery. Sustainable Computing: Informatics and Systems 38, 100858. — F1 ≈ 90 % ; YOLO F1 0,89 sur Svalbard vs 0,57 (Hough), 0,43 (DBSCAN), 0,71 (template matching).",
  "Boulent J., Charry B., Kennedy M.M. et al. (2023). Scaling whale monitoring using deep learning: a human-in-the-loop solution for analyzing aerial datasets. Frontiers in Marine Science 10:1099479. — 5 334 images aériennes (bélugas, Cumberland Sound) ; 4 051 détections communes sur 4 572 (observateur) et 4 298 (pipeline) ; biais de détection variable entre observateurs expérimentés.",
  "Fu J., Gauthier A.M., Marcoux M. et al. (2024). Localization and tracking of beluga whales in aerial video using deep learning. Frontiers in Marine Science 11:1445698. — YOLOv7 : précision 93,4 %, rappel 91,2 % (toutes classes) ; F1 0,92 ; travaux antérieurs YOLOv4 : 74 % / 72 %.",
  "Kellenberger B., Marcos D., Tuia D. (2018). Detecting mammals in UAV images: best practices to address a substantially imbalanced dataset with deep learning. Remote Sensing of Environment 216, 139-153. arXiv:1806.11368. — à 80 % de rappel, faux positifs réduits de > 2 500 à < 450 ; à 90 % de rappel, 870 détections contre 20 688 pour la base.",
  "Delplanque A., Foucher S., Théau J., Bussière E., Vermeulen C., Lejeune P. (2023). From crowd to herd counting: how to precisely detect and count African mammals using aerial imagery and deep learning? ISPRS J. Photogramm. Remote Sens. 197, 167-180. — HerdNet F1 global 73,6 % sur images 24 Mpx ; nécessite un ré-entraînement pour tout changement d'angle de vue, d'espèce ou de résolution.",
  "Gray P.C., Fleishman A.B., Klein D.J. et al. (2019). A convolutional neural network for detecting sea turtles in drone imagery. Methods in Ecology and Evolution 10(3), 345-355. — 944 exemples d'entraînement ; +8 % de tortues détectées par rapport au comptage manuel ; charge de validation réduite de 2 971 554 à 44 822 fenêtres.",
  "Cubaynes H.C., Fretwell P.T. (2022). Whales from space dataset, an annotated satellite image dataset of whales for training machine learning models. Scientific Data 9, 245 ; Cubaynes H.C. et al. (2023). Annotating very high-resolution satellite imagery: a whale case study. MethodsX 10, 102040. — 633 baleines annotées (boîtes + points), 4 espèces, 4 capteurs ; protocole d'annotation standardisé avec niveaux de certitude.",
  "Jaiswal A., Wu Y., Natarajan P., Natarajan P. (2021). Class-agnostic Object Detection. WACV 2021. arXiv:2011.14204. — apprentissage adversarial retirant l'information de classe des caractéristiques ; meilleure détection des classes non vues.",
  "Kim D., Lin T.-Y., Angelova A., Kweon I.S., Kuo W. (2022). Learning Open-World Object Proposals without Learning to Classify. IEEE RA-L / ICRA 2022. arXiv:2108.06753. — OLN : objectness par centralité/IoU sans classification ; généralisation cross-dataset (COCO → Objects365, RoboNet, EpicKitchens).",
  "Liu S., Zeng Z., Ren T. et al. (2024). Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection. ECCV 2024. — 52,5 AP zero-shot sur COCO, 26,1 AP moyen zero-shot sur ODinW (35 domaines).",
  "Beery S., Van Horn G., Perona P. (2018). Recognition in Terra Incognita. ECCV 2018. arXiv:1807.04975. — excellentes performances sur les lieux d'entraînement, généralisation médiocre à de nouveaux lieux (pièges photographiques).",
  "Chen Y., Li W., Sakaridis C., Dai D., Van Gool L. (2018). Domain Adaptive Faster R-CNN for Object Detection in the Wild. CVPR 2018 ; et Su P. et al. (2020) Adapting Object Detectors with Conditional Domain Normalization, arXiv:2003.07071. — Cityscapes → Foggy Cityscapes : source seule 26,1 mAP, adapté 27,9 mAP (chiffres CDN).",
  "Li J., Xiong C., Socher R., Hoi S. (2020). Towards Noise-resistant Object Detection with Noisy Annotations. arXiv:2003.01285 ; et Robust Tiny Object Detection in Aerial Images amidst Label Noise (2024), arXiv:2401.08056. — sous 40 % de bruit de boîte, l'IoU moyen bruit/propre n'est que de 0,45 ; les détecteurs sont robustes aux étiquettes manquantes (< 2 points de mAP à 60 % de bruit) mais le mAP chute de près de moitié à 30 % de boîtes inexactes.",
  "Kim Y. et al. (2024). NBBOX: Noisy Bounding Box Improves Remote Sensing Object Detection. arXiv:2409.09424. — écart entre boîte annotée et boîte englobante minimale ; transformations de boîtes comme régularisation en imagerie aérienne.",
  "Why Domain Matters: a preliminary study of domain effects in underwater object detection (2026), arXiv:2604.26174 ; et Domain-Aware Benchmarking of Underwater Object Detection and Annotation Quality, arXiv:2607.10575. — visibilité et échelle sont les premiers facteurs de variation des performances en sous-marin.",
  "Han J., Ding J., Xue N., Xia G.-S. (2021). ReDet: A Rotation-equivariant Detector for Aerial Object Detection. CVPR 2021. arXiv:2103.07733 ; Wu et al. (2025) Measuring the Impact of Rotation Equivariance on Aerial Object Detection, ICCV 2025. — +1,2 / +3,5 / +2,6 mAP sur DOTA-v1.0, DOTA-v1.5, HRSC2016.",
  "Maritime Small Object Detection from UAVs using Deep Learning with Altitude-Aware Dynamic Tiling (2025). arXiv:2511.19728. — SeaDronesSee : +38 % de mAP50_small par tuilage (YOLOv5 + SAHI) par rapport à l'absence de tuilage.",
  "Systematic evaluation / drone small object studies (2025-2026) : résolution d'entrée 640 → 1280 px : mAP50 de 12,7 % à 15,9 % (+25 % relatif) pour un coût ×4 ; taille des objets ~10 px → ~20 px. Sources : arXiv:2504.19347, arXiv:2603.02142, Sci. Rep. s41598-025-31803-7.",
  "UAV-DETR (Sensors 2025, doi:10.3390/s25154582) ; ACD-DETR (2025) ; RT-UAV-SOD (Sci. Rep. 2025). — sur VisDrone2019-DET, RT-DETR-R18 de base ≈ 47–48 mAP@0,5 ; variantes UAV 50,9–51,6 mAP@0,5 (+3,5 points).",
  "Wang X. et al. (2024). A review of deep learning techniques for detecting animals in aerial and satellite images. Int. J. Appl. Earth Obs. Geoinf. ; et Deep learning methods for detecting marine vertebrates and invertebrates from satellite, aerial and underwater imagery: a review (2026), Deep-Sea Research I. — défis principaux : jeux déséquilibrés, petits objets, méthodes d'annotation, fond d'image, comptage, estimation d'incertitude.",
  "Zhu P., Wen L., Du D. et al. (2021). Detection and Tracking Meet Drones Challenge. IEEE TPAMI 43(11) ; Xia G.-S. et al. (2018/2021) DOTA. — benchmarks aériens non marins de référence (VisDrone-DET 10 209 images ; DOTA-v2.0 11 268 images, 1,79 M instances).",
  "Wei et al. (2022). Detection and tracking of belugas, kayaks and motorized boats in drone video using deep learning. J. Unmanned Vehicle Systems ; et Machine-learning approach for automatic detection of wild beluga whales from hand-held camera pictures (Sensors 2022). — vagues, ombres, écume et reflets solaires sont visuellement proches des baleines ; au-delà de Beaufort 4, les moutons rendent la discrimination difficile.",
  "Audit interne GoldenEye (ce dépôt, inventory_report.md, 2026-09-09). — côté relatif médian des objets : 0,96 % (phoques NOAA, 14 311 boîtes, images 6576×4384), 0,99 % (oiseaux drone 5472×3648), 8,4 % (mêmes oiseaux en tuiles 684×521), 4,4 % (poissons estuaire NOAA, 1920×1080), 32,7 % (poissons multi-sources), 2,5 % (bélugas satellite, chips 320 px), 21 % (Whales from space, chips 128 px) ; 91 % d'images vides en relevé aérien ; aspect médian 1,7–2,1 en sous-marin contre ≈ 1 en nadir.",
];

// ---------------------------------------------------------------- contenu
const children = [];
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 200 }, children: [new TextRun({ text: "Projet GoldenEye — SogetiLabs", font: FONT, size: 28, color: "1F4E79" })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 }, children: [new TextRun({ text: "Hypothèses a priori sur la généralisation cross-domaine d'un détecteur class-agnostic (RT-DETRv2)", font: FONT, size: 40, bold: true })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "Revue de la littérature scientifique et prédictions chiffrées à confirmer par les tests", font: FONT, size: 26, italics: true })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: "Sous-marin → aérien → satellite", font: FONT, size: 24 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 1200, after: 100 }, children: [new TextRun({ text: "Version 1.0 — 9 septembre 2026", font: FONT, size: 22 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Document de travail préparatoire — 32 références, 12 hypothèses, 9 expériences", font: FONT, size: 20, color: "595959" })] }));
children.push(new Paragraph({ children: [new PageBreak()] }));

children.push(H1("Sommaire"));
children.push(new TableOfContents("Sommaire", { hyperlink: true, headingStyleRange: "1-2" }));
children.push(new Paragraph({ children: [new PageBreak()] }));

// 1
children.push(H1("1. Objet du document et méthode"));
children.push(P("Ce document fixe, avant les tests de généralisation cross-domaine du détecteur RT-DETRv2 entraîné en sous-marin, un ensemble d'hypothèses chiffrées fondées sur la littérature. Chaque hypothèse est formulée de façon réfutable : une prédiction numérique, l'expérience qui la teste dans le dépôt Bmark_Sogeti, et le critère qui la confirme ou l'infirme. L'objectif est double : éviter d'interpréter l'écart 90 % → 58 % sans cadre de référence, et disposer, une fois les résultats obtenus, d'une grille de lecture déjà écrite."));
children.push(P("Trois familles de sources sont mobilisées : (a) les articles fondateurs des architectures et des métriques (RT-DETR, DETR et petits objets, tuilage SAHI, distance de Wasserstein normalisée, détection class-agnostic, adaptation de domaine) ; (b) les travaux appliqués à la mégafaune marine depuis l'avion, le drone et le satellite (Borowicz 2019, Guirado 2019, Green 2023, Boulent 2023, Fu 2024, Zheng 2025, Kapoor 2023, Cubaynes 2022-2023) et à la faune terrestre aérienne (Kellenberger 2018, Delplanque 2023, Gray 2019, Wu 2022) ; (c) l'audit interne des conventions d'annotation réalisé sur les jeux publics récupérés (inventory_report.md), qui fournit les ordres de grandeur d'échelle relative propres au projet."));
children.push(P([R("Limite de méthode. ", { bold: true }), R("Les bases bibliographiques (Semantic Scholar, OpenAlex, Crossref, arXiv, Europe PMC) et les sites des éditeurs étaient inaccessibles depuis l'environnement d'exécution ; les chiffres cités proviennent des résumés, pages d'articles et extraits indexés par la recherche web. Les valeurs sont données telles que publiées, avec leur source numérotée ; les quelques valeurs recomposées à partir d'un article secondaire sont signalées « à vérifier sur le texte intégral ». Aucun chiffre n'a été inventé : lorsqu'une source ne donnait pas de nombre, l'hypothèse le dit.")]));

// 2
children.push(H1("2. Cadre du projet et faits déjà établis"));
children.push(H2("2.1 Le modèle et l'écart observé"));
children.push(P("Le détecteur est un RT-DETRv2 (transformeur de détection temps réel, famille RT-DETR [1][2]) entraîné en détection class-agnostic sur des images sous-marines uniquement. Sur COCO, RT-DETR-R50 atteint 53,1 AP, mais avec une forte dépendance à la taille : AP_S 34,8, AP_M 58,2, AP_L 71,0 [1]. L'AP sur petits objets vaut donc environ la moitié de l'AP sur grands objets pour le même modèle, avant tout décalage de domaine. Les performances internes rapportées sont d'environ 90 % en sous-marin et 58 % en aérien (métrique interne à préciser lors des tests : mAP@0,5, F1 ou rappel)."));
children.push(H2("2.2 Ce que l'audit interne des conventions a déjà mesuré"));
children.push(P("L'audit des jeux publics de substitution [32] établit trois écarts de convention entre domaines, indépendants du modèle :"));
children.push(B([R("Échelle relative. ", { bold: true }), R("Le côté équivalent médian d'un objet vaut 4,4 % à 33 % du côté image en sous-marin, 0,96 % en aérien plein cadre (phoques NOAA à 6576×4384, oiseaux drone à 5472×3648), 2,5 % à 21 % en satellite selon la taille des chips. Redimensionné à 640 px, un phoque aérien mesure environ 5 px de côté. Le test de Kolmogorov-Smirnov entre sous-marin et aérien donne D ≥ 0,95.")]));
children.push(B([R("Densité. ", { bold: true }), R("91 % des images d'un relevé aérien sont vides ; les images annotées portent 2 à 12 objets. En vidéo sous-marine, 61 à 65 % des trames sont vides.")]));
children.push(B([R("Forme. ", { bold: true }), R("Ratio d'aspect médian 1,7 à 2,1 (objets allongés, vue latérale) en sous-marin contre ≈ 1 en vue nadir, où l'orientation est uniforme.")]));
children.push(P("Le tuilage ramène les mêmes objets aériens de 1 % à 8,4 % du côté image (tuiles 684 px), c'est-à-dire dans la gamme sous-marine. Ce fait guide la majorité des hypothèses ci-dessous."));

// 3 état de l'art
children.push(H1("3. État de l'art : ce que la littérature permet d'anticiper"));
children.push(H2("3.1 Détecteurs DETR et petits objets"));
children.push(P("Les DETR sont structurellement moins bons que les détecteurs à pyramide de caractéristiques sur les petits objets, faute de FPN et à cause du coût de l'attention à haute résolution ; RT-DETR corrige partiellement le problème par son encodeur hybride, mais l'écart AP_S / AP_L reste de 1 à 2 [1]. Les variantes dédiées aux drones (UAV-DETR, ACD-DETR, RT-UAV-SOD) gagnent environ +3,5 points de mAP@0,5 sur VisDrone2019-DET par rapport au RT-DETR de base, qui plafonne autour de 47-48 mAP@0,5 sur ce benchmark aérien [28]. Le levier le plus fiable reste la résolution d'entrée : passer de 640 à 1280 px double la taille apparente des objets (≈ 10 px → ≈ 20 px) et augmente le mAP50 de 12,7 à 15,9 % dans une étude drone, pour un coût de calcul ×4 [27]."));
children.push(H2("3.2 Échelle, résolution au sol et seuil de détectabilité"));
children.push(P("Wu et al. [5] montrent, en dégradant des images drone d'animaux d'élevage vers des GSD croissantes, que la performance d'un YOLOv5 chute brutalement autour de 0,5 m/px (mAP −52 % dans la configuration la plus défavorable). Pour les objets minuscules, la métrique elle-même devient instable : un objet de 6×6 px voit son IoU chuter de 0,53 à 0,06 pour une déviation de localisation d'un pixel [4], ce qui pénalise à la fois l'assignation des étiquettes à l'entraînement et l'évaluation à IoU 0,5. Sur le benchmark AI-TOD (objets < 16 px), l'état de l'art n'atteint que 24,8 AP [4]. En satellite, les animaux de plus de 0,6 m sont détectables en imagerie sub-métrique, et la mer au-delà de Beaufort 4 produit des moutons de la taille d'une baleine [31]."));
children.push(H2("3.3 Tuilage et inférence par découpage"));
children.push(P("SAHI [3] applique un détecteur inchangé sur des tuiles chevauchantes : +6,8 / +5,1 / +5,3 AP sur VisDrone et xView pour FCOS, VFNet et TOOD sans ré-entraînement, et +12,7 / +13,4 / +14,5 AP cumulés après fine-tuning sur tuiles. En contexte maritime (SeaDronesSee, drones entre 5 et 260 m d'altitude), le tuilage améliore le mAP50 des petits objets de 38 % relatif [26]. Ces gains proviennent du même mécanisme que celui identifié dans l'audit : le tuilage rétablit l'échelle relative des objets."));
children.push(H2("3.4 Détection class-agnostic, objectness et généralisation"));
children.push(P("Jaiswal et al. [17] formalisent la détection class-agnostic et montrent qu'un apprentissage adversarial retirant l'information de classe des caractéristiques améliore la détection de classes non vues. OLN [18] remplace la classification par une estimation d'objectness (centralité, IoU) et généralise mieux d'un jeu à l'autre (COCO → Objects365, RoboNet, EpicKitchens). Ces travaux justifient le choix CAOD de GoldenEye, mais ils mesurent une généralisation sémantique (nouvelles classes) dans des images naturelles au sol ; aucun ne teste un changement de point de vue et de milieu aussi radical que sous-marin → nadir. Les modèles de fondation ouverts donnent un ordre de grandeur du prix d'un domaine inhabituel : Grounding DINO passe de 52,5 AP zero-shot sur COCO à 26,1 AP moyen sur les 35 domaines d'ODinW [19]."));
children.push(H2("3.5 Décalage de domaine et adaptation"));
children.push(P("Beery et al. [20] établissent qu'en pièges photographiques, des modèles excellents sur leurs lieux d'entraînement généralisent mal à de nouveaux lieux, même sans changement de capteur ni de point de vue. En adaptation de domaine pour la détection, la référence Cityscapes → Foggy Cityscapes donne 26,1 mAP en source seule contre 27,9 avec DA-Faster (chiffres rapportés par [21], à vérifier sur le texte intégral) ; les méthodes contrastives récentes en imagerie satellite gagnent jusqu'à +7,4 mAP [source « Domain Adaptation with Contrastive Learning for Object Detection in Satellite Imagery », 2023]. En sous-marin, les premiers benchmarks « domain-aware » [24] identifient la visibilité et l'échelle comme facteurs dominants de variation. Delplanque et al. [14] notent explicitement que HerdNet exige un ré-entraînement pour tout changement d'angle de vue, d'espèce ou de résolution spatiale."));
children.push(H2("3.6 Mégafaune marine : niveaux de performance publiés"));
children.push(table(
  ["Étude", "Plateforme", "Modèle", "Résultat publié"],
  [
    ["Borowicz 2019 [6]", "aérien → satellite WV-3 31 cm", "ResNet / DenseNet (classification de tuiles)", "100 % des tuiles baleine, 94 % des tuiles eau ; F1 0,968"],
    ["Guirado 2019 [7]", "satellite + aérien (Google Earth, Arkive, NOAA)", "Inception v3 + Faster R-CNN Inception-ResNet", "F1 0,81 détection, 0,94 comptage"],
    ["Green 2023 [8]", "satellite Maxar + drone", "YOLOv5", "entraînement combiné ; 503 baleines au total (chiffres P/R non accessibles)"],
    ["Kapoor 2023 [10]", "satellite", "YOLO", "F1 ≈ 0,90 ; 0,89 sur Svalbard vs 0,43–0,71 pour les méthodes classiques"],
    ["Zheng 2025 [9]", "satellite VHR panchromatique, chips 320 px", "YOLOv8 (boîtes SAM)", "F1 72,2 % bélugas, 70,3 % phoques"],
    ["Boulent 2023 [11]", "aérien avion, 5 334 images", "détecteur + humain dans la boucle", "4 051 détections communes / 4 572 (observateur) / 4 298 (pipeline)"],
    ["Fu 2024 [12]", "drone vidéo, bélugas", "YOLOv7", "P 93,4 %, R 91,2 %, F1 0,92 (YOLOv4 antérieur : 74 % / 72 %)"],
    ["Kellenberger 2018 [13]", "drone eBee, Namibie, mammifères", "CNN + gestion du déséquilibre", "à 80 % de rappel : FP > 2 500 → < 450 ; à 90 % : 870 vs 20 688"],
    ["Delplanque 2023 [14]", "avion oblique, troupeaux", "HerdNet (points)", "F1 73,6 % sur images 24 Mpx"],
    ["Gray 2019 [15]", "drone, tortues (NIR)", "CNN, 944 exemples", "+8 % vs comptage manuel ; validation 2,97 M → 44 822 fenêtres"],
  ], [1700, 2300, 2400, 3200]));
children.push(gap());
children.push(P("Deux enseignements : (i) les meilleurs résultats aériens et satellite (F1 0,90–0,97) sont obtenus par des modèles entraînés ou ré-entraînés dans le domaine cible, souvent à l'échelle de tuiles ; (ii) le seul transfert inter-domaines documenté qui réussit sans adaptation, Borowicz 2019, repose sur un appariement explicite de la résolution au sol (imagerie aérienne sous-échantillonnée à la GSD satellite)."));
children.push(H2("3.7 Qualité et convention des annotations"));
children.push(P("Les détecteurs tolèrent les étiquettes manquantes (moins de 2 points de mAP perdus à 60 % d'omissions sur objets minuscules) mais pas les boîtes inexactes : à 30 % de boîtes bruitées, le mAP chute de près de moitié, et à 40 % de bruit l'IoU moyen entre boîte bruitée et boîte propre n'est que de 0,45 [22]. En imagerie aérienne, l'écart entre boîte annotée et boîte englobante minimale est fréquent et justifie des transformations de boîtes comme régularisation [23]. Zheng et al. [9] montrent que des boîtes ajustées par SAM à partir de points surpassent nettement des boîtes tampon fixes, et Boulent et al. [11] rappellent que même des observateurs expérimentés ont des biais de détection différents. Cubaynes et al. [16] proposent un protocole standardisé (niveaux de certitude, boîtes et points) précisément pour réduire cette variabilité."));

// 4 hypothèses
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("4. Hypothèses a priori et prédictions chiffrées"));
children.push(P("Chaque hypothèse suit le même format : énoncé, prédiction, fondement, expérience de test (référence aux scripts du dépôt), critère de décision. Les prédictions sont des intervalles a priori, pas des promesses : un résultat hors intervalle est une information, à documenter comme tel."));

const hyps = [
  {
    id: "H1", titre: "L'écart 90 → 58 est majoritairement un artefact d'échelle si l'aérien interne est en plein cadre",
    enonce: "Si les 478 images aériennes internes sont des pleins cadres de relevé (objets ≈ 1 % du côté image, comme les phoques NOAA), le RT-DETRv2 évalué à 640 px voit des objets de 5 à 8 px et l'essentiel de la perte vient de l'échelle, non de l'apparence sous-marine/aérienne.",
    prediction: "Sur les pleins cadres NOAA à 640 px : rappel ≤ 20 % et AP@0,5 ≤ 10. Sur les mêmes images tuilées à 640 px (objets ≈ 8 % du côté) : rappel ≥ 60 %, AP@0,5 multiplié par 3 au moins. Sur les données internes, si l'audit donne un côté relatif médian < 2 %, plus de la moitié de l'écart 90 → 58 sera récupérée par le seul tuilage.",
    fondement: "AP_S ≈ AP_L / 2 pour RT-DETR [1] ; effondrement autour de 0,5 m/px [5] ; instabilité de l'IoU sous 10 px [4] ; +5 à +15 AP par tuilage [3] ; +38 % relatif sur petits objets maritimes [26] ; audit interne [32].",
    test: "E1 : audit_dataset.py sur data/aerien/local (côté relatif p50). E2 : inférence RT-DETRv2 sur noaa_arctic_seals_sample en plein cadre puis en tuiles 640/1024 px avec chevauchement 20 % ; mêmes métriques sur l'aérien interne.",
    critere: "Confirmée si le gain de tuilage ≥ 20 points de rappel et si l'AP par tranche COCO (small/medium/large) suit l'ordre small < medium < large avec un rapport ≤ 0,6. Infirmée si le tuilage gagne < 5 points : l'écart est alors un décalage d'apparence (voir H5).",
  },
  {
    id: "H2", titre: "Le tuilage à l'inférence, sans ré-entraînement, apporte +5 à +15 points d'AP en aérien",
    enonce: "L'inférence par tuiles chevauchantes (type SAHI) appliquée au modèle sous-marin inchangé améliore la détection aérienne dans la fourchette publiée pour les détecteurs génériques.",
    prediction: "+5 à +15 points d'AP@0,5 sur aérien plein cadre ; gain nul ou négatif (−2 à 0) sur des images déjà tuilées ou rapprochées ; +30 à +40 % relatif sur la tranche « small ». Le fine-tuning sur tuiles, hors périmètre de cette phase, doublerait le gain (+12 à +15 AP) [3].",
    fondement: "SAHI [3] ; SeaDronesSee [26] ; résolution 640 → 1280 [27].",
    test: "E2 (grille de tailles de tuiles 512 / 640 / 1024 px, chevauchement 0,1 / 0,2 / 0,3) sur NOAA seals, UAS waterfowl experts et aérien interne.",
    critere: "Confirmée si le meilleur réglage de tuile gagne ≥ 5 AP@0,5 sur au moins deux jeux. La taille de tuile optimale doit placer le côté relatif médian des objets entre 3 % et 10 % de la tuile.",
  },
  {
    id: "H3", titre: "La performance par tranche de taille reproduit la hiérarchie COCO : AP_S ≈ 0,5 × AP_L",
    enonce: "Indépendamment du domaine, le rapport AP_S / AP_L du RT-DETRv2 se situe entre 0,4 et 0,6, et la répartition des objets par tranche explique une part prévisible de la performance globale.",
    prediction: "Sous-marin : ≥ 70 % d'objets « large » (≥ 96² px) ; aérien natif : ≥ 95 % « small » ou « medium ». Rapport AP_S / AP_L entre 0,4 et 0,6 dans chaque domaine où les trois tranches sont peuplées.",
    fondement: "RT-DETR-R50 : 34,8 / 58,2 / 71,0 [1] ; audit : 74,9 % « large » en sous-marin multi-sources, 97 % « medium » pour les phoques natifs [32].",
    test: "E3 : évaluation COCO complète (AP, AP_S, AP_M, AP_L) via pycocotools sur chaque jeu normalisé (coco_objet*.json).",
    critere: "Confirmée si le rapport tombe dans [0,4 ; 0,6]. Un rapport < 0,3 signale une pénalité additionnelle propre au domaine (fond, texture) sur les petits objets.",
  },
  {
    id: "H4", titre: "Part de l'écart imputable à la convention : règle de décision",
    enonce: "La part de l'écart 90 → 58 attribuable aux conventions (échelle, images vides, boîtes) se déduit de la performance aérienne mesurée à échelle appariée avec le sous-marin.",
    prediction: "Écart résiduel après appariement d'échelle (tuilage réglé pour un côté relatif médian de 4 à 8 %) : 10 à 25 points, soit une part « convention » de 40 à 70 % de l'écart initial si l'aérien interne est plein cadre, et de 0 à 20 % s'il est déjà tuilé.",
    fondement: "Combinaison de H1-H3 ; écarts source-seule vs adapté en adaptation de domaine (≈ 2 à 8 points) [21] ; ODinW [19] ; Delplanque [14].",
    test: "E4 : calcul écart_total − écart_à_échelle_appariée sur l'aérien interne ; même calcul sur NOAA seals comme contrôle externe.",
    critere: "Part « convention » = (perf_appariée − perf_native) / (perf_sous-marin − perf_native). Rapporter l'intervalle de confiance par bootstrap sur les images (≥ 1 000 tirages).",
  },
  {
    id: "H5", titre: "Un décalage de domaine d'apparence subsiste après appariement d'échelle",
    enonce: "Même à échelle égale, le fond (eau vue du dessus, glace, moutons, reflets), la texture et la silhouette nadir diffèrent du sous-marin ; une perte irréductible sans adaptation demeure.",
    prediction: "Perte résiduelle de 10 à 25 points d'AP@0,5 par rapport au sous-marin, du même ordre que la chute COCO → ODinW d'un modèle ouvert (52,5 → 26,1) rapportée à l'échelle du problème [19]. Sur satellite, perte résiduelle plus forte (20 à 40 points).",
    fondement: "Beery [20] ; benchmarks d'adaptation [21] ; Delplanque [14] ; facteurs visibilité/échelle en sous-marin [24].",
    test: "E4 et E5 : comparaison à échelle appariée entre sous-marin (poissons NOAA et interne), aérien (phoques, oiseaux) et satellite (bélugas SAM, Whales from space).",
    critere: "Confirmée si la perte résiduelle est ≥ 10 points sur tous les jeux aériens à échelle appariée. Si < 5 points, la convention explique quasiment tout et H4 est révisée à la hausse.",
  },
  {
    id: "H6", titre: "Les faux positifs sur la surface de l'eau dominent l'erreur aérienne, pas les manques",
    enonce: "Sur un relevé où 91 % des images sont vides, un détecteur class-agnostic entraîné sur des fonds sous-marins produit des faux positifs sur moutons, reflets, écume et glace ; la précision chute plus vite que le rappel.",
    prediction: "À 80 % de rappel : ≥ 1 faux positif par image sur l'ensemble du relevé NOAA (44 185 images), soit plusieurs dizaines de milliers de fausses alarmes ; précision ≤ 30 % sans filtrage. Après seuil optimal, F1 entre 0,3 et 0,6 pour le modèle non adapté.",
    fondement: "Kellenberger : 20 688 détections à 90 % de rappel pour la base [13] ; nature des distracteurs [31] ; Beaufort > 4 [31] ; 91 % d'images vides [32].",
    test: "E6 : inférence sur l'échantillon NOAA complet (202 annotées + 14 vides) puis sur 1 000 images vides supplémentaires tirées au hasard (script fetch_lila_noaa_seals_sample.py --n-empty 1000) ; courbe précision-rappel et FP/image par vol et par caméra.",
    critere: "Confirmée si FP/image ≥ 1 à 80 % de rappel. Documenter la nature des FP par inspection visuelle de 100 cas (moutons, glace, reflets, bord de tuile).",
  },
  {
    id: "H7", titre: "Le prior de forme appris en sous-marin (objets allongés) pénalise les objets nadir quasi carrés",
    enonce: "Le modèle a appris des boîtes de ratio 1,7 à 2,1 ; les objets nadir (ratio ≈ 1, orientation uniforme) sont moins bien rappelés, et l'augmentation par rotation à l'inférence réduit l'écart.",
    prediction: "Rappel inférieur de 5 à 15 points pour les objets de ratio dans [0,7 ; 1,4] par rapport aux objets de ratio > 1,7 dans le même jeu aérien. Gain de +1 à +4 points d'AP par TTA de rotation (0°, 90°, 180°, 270° + fusion), cohérent avec les gains d'équivariance rotationnelle publiés [25].",
    fondement: "Audit des ratios [32] ; ReDet et mesures d'équivariance [25].",
    test: "E7 : rappel par tranche de ratio (boxes.csv de l'audit croisé avec les détections) ; TTA rotation.",
    critere: "Confirmée si l'écart de rappel entre tranches ≥ 5 points ou si la TTA gagne ≥ 1 point. Infirmée si les deux effets sont < 1 point.",
  },
  {
    id: "H8", titre: "Le choix class-agnostic limite la perte cross-domaine par rapport à un détecteur multi-classes",
    enonce: "À entraînement égal, le modèle class-agnostic conserve un rappel cross-domaine supérieur à un modèle à classes, parce qu'il ne supprime pas les objets non reconnus comme fond.",
    prediction: "AR@100 cross-domaine supérieur de 5 à 10 points pour la version class-agnostic ; écart de précision faible ou inversé.",
    fondement: "Jaiswal [17] ; OLN [18] ; enquêtes open-world [17][18].",
    test: "E8 (optionnelle, nécessite un entraînement de contrôle hors périmètre de cette phase) : entraîner une variante multi-classes sur le même jeu sous-marin, comparer AR@100 en aérien.",
    critere: "Confirmée si l'écart d'AR@100 ≥ 5 points. À défaut d'entraînement, mesurer AR@100 du modèle actuel comme borne de référence pour les phases suivantes.",
  },
  {
    id: "H9", titre: "Un modèle de fondation ouvert zero-shot donne une borne de référence de 20 à 40 AP@0,5 en aérien",
    enonce: "Grounding DINO (prompts « seal », « whale », « animal ») évalué sans entraînement fournit un plancher raisonnable ; le modèle interne doit le dépasser à échelle appariée, sinon le bénéfice du pré-entraînement sous-marin est nul en aérien.",
    prediction: "AP@0,5 zero-shot entre 20 et 40 sur tuiles aériennes, < 15 sur pleins cadres, < 10 sur satellite ; cohérent avec la moyenne ODinW (26,1) [19].",
    fondement: "Grounding DINO [19] ; applications zero-shot en télédétection et sur oiseaux 2024-2025.",
    test: "E9 : inférence Grounding DINO sur les mêmes tuiles que E2, mêmes métriques.",
    critere: "Si le RT-DETRv2 sous-marin à échelle appariée < Grounding DINO zero-shot, le transfert sous-marin → aérien est jugé non bénéfique et la phase suivante doit partir d'un modèle ouvert ou d'un pré-entraînement aérien.",
  },
  {
    id: "H10", titre: "Le satellite est le domaine le plus dégradé ; un sur-échantillonnage ×2 des chips rend le transfert mesurable",
    enonce: "Sur chips satellite (objets 5 à 30 px), le modèle sous-marin non adapté est proche de zéro à résolution native ; un sur-échantillonnage ×2 à ×4 des chips fait remonter le rappel.",
    prediction: "Rappel < 10 % à résolution native sur bélugas (7 px) ; 20 à 50 % après sur-échantillonnage ×2 à ×4 ; 40 à 70 % sur Whales from space (chips 128 px, objets 30 px). Pour comparaison, les modèles entraînés dans le domaine atteignent F1 0,72 à 0,97 [6][7][9][10].",
    fondement: "Tableau 3.6 ; NWD [4] ; audit des chips [32].",
    test: "E5 : inférence sur beluga_seeker (4 images disponibles, annotations complètes pour extension) et WSDataset, à ×1, ×2, ×4.",
    critere: "Confirmée si le rappel croît de façon monotone avec le facteur de sur-échantillonnage et dépasse 20 % à ×2.",
  },
  {
    id: "H11", titre: "La sensibilité de l'IoU aux petits objets fausse la mesure : évaluer aussi à IoU 0,3 et avec NWD",
    enonce: "Une part de l'écart mesuré à IoU 0,5 provient de la métrique elle-même sur des objets de moins de 15 px ; des seuils plus tolérants ou une métrique gaussienne réduisent l'écart sans changer le modèle.",
    prediction: "Écart AP@0,3 − AP@0,5 ≥ 10 points sur aérien natif et satellite, ≤ 3 points en sous-marin. Le classement des jeux est inchangé, mais la part « convention » de H4 augmente de 5 à 10 points quand on évalue à IoU 0,3.",
    fondement: "NWD [4] ; bruit de boîte [22] ; boîtes lâches en aérien [23].",
    test: "E3 étendu : AP à IoU 0,3 / 0,5 / 0,75 et NWD sur tous les jeux.",
    critere: "Confirmée si la différence AP@0,3 − AP@0,5 est au moins trois fois plus grande en aérien natif qu'en sous-marin.",
  },
  {
    id: "H12", titre: "La qualité des boîtes internes conditionne les résultats : un taux de boîtes hors cadre ou lâches > 10 % coûte plusieurs points",
    enonce: "Si l'audit interne révèle des boîtes hors cadre, dégénérées ou systématiquement plus larges que l'objet, l'évaluation sous-estime le modèle et l'entraînement futur en souffrira.",
    prediction: "Chaque tranche de 10 % de boîtes inexactes (IoU < 0,5 avec la boîte serrée) coûte 3 à 8 points d'AP@0,5 ; à 30 % le mAP est presque divisé par deux [22]. Les jeux publics récupérés montrent 0,4 % (phoques) à 14 % (tuiles d'oiseaux) de boîtes hors cadre [32].",
    fondement: "Li 2020 et suites [22] ; NBBOX [23] ; SAM vs tampons [9].",
    test: "E1 (audit) puis ré-annotation d'un échantillon de 50 images internes par deux annotateurs ; IoU moyen entre annotateurs et avec la boîte SAM.",
    critere: "Si l'IoU inter-annotateurs < 0,7 ou si > 10 % des boîtes sont hors cadre ou dégénérées, corriger les annotations avant toute conclusion sur le modèle.",
  },
];

for (const h of hyps) {
  children.push(H2(`${h.id}. ${h.titre}`));
  children.push(P([R("Énoncé. ", { bold: true }), R(h.enonce)]));
  children.push(P([R("Prédiction a priori. ", { bold: true, color: "1F4E79" }), R(h.prediction)]));
  children.push(P([R("Fondement. ", { bold: true }), R(h.fondement)]));
  children.push(P([R("Expérience. ", { bold: true }), R(h.test)]));
  children.push(P([R("Critère de décision. ", { bold: true }), R(h.critere)]));
}

// 5 protocole
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("5. Protocole de test proposé"));
children.push(P("Les expériences ci-dessous n'entraînent aucun modèle (sauf E8, optionnelle et explicitement hors phase). Elles utilisent les scripts du dépôt pour la préparation et une boucle d'inférence RT-DETRv2 à écrire (scripts/eval_rtdetr.py, à créer : entrée COCO classe unique, sortie détections COCO, évaluation pycocotools)."));
children.push(table(
  ["Exp.", "Hypothèses", "Jeux", "Variables", "Métriques", "Sortie attendue"],
  [
    ["E1", "H1, H4, H12", "sous-marin interne, aérien interne (478)", "aucune : audit", "côté relatif p5-p95, densité, ratio, boîtes hors cadre", "audits/*/summary.json, 20 PNG aériens"],
    ["E2", "H1, H2", "NOAA seals (202 img), UAS experts (12), aérien interne", "tuile 512/640/1024, chevauchement 0,1/0,2/0,3, plein cadre", "AP@0,5, rappel, FP/img par tranche COCO", "courbes AP vs taille de tuile"],
    ["E3", "H3, H11", "tous les COCO normalisés", "seuil IoU 0,3/0,5/0,75, NWD", "AP, AP_S/M/L, AR@100", "table par jeu × seuil"],
    ["E4", "H4, H5", "sous-marin vs aérien à échelle appariée", "tuilage réglé pour p50 côté relatif 4-8 %", "écart d'AP, IC bootstrap", "part « convention » chiffrée"],
    ["E5", "H5, H10", "beluga_seeker, WSDataset", "sur-échantillonnage ×1/×2/×4", "rappel, AP@0,3", "courbe rappel vs facteur"],
    ["E6", "H6", "NOAA seals + 1 000 images vides", "seuil de confiance", "précision-rappel, FP/img par vol", "typologie des FP (100 cas)"],
    ["E7", "H7", "aérien interne, NOAA seals", "TTA rotation 0/90/180/270", "rappel par tranche de ratio", "gain TTA"],
    ["E8 (opt.)", "H8", "sous-marin interne", "entraînement multi-classes de contrôle", "AR@100 cross-domaine", "hors phase actuelle"],
    ["E9", "H9", "mêmes tuiles que E2", "prompts « seal », « whale », « animal »", "AP@0,5 zero-shot", "plancher de référence"],
  ], [800, 1200, 2000, 1900, 1900, 1800]));
children.push(gap());
children.push(P([R("Ordre recommandé. ", { bold: true }), R("E1 d'abord (il conditionne l'interprétation de tout le reste), puis E2 et E3 le même jour (même boucle d'inférence), E6 en tâche de fond (volume), E4 et E11 en post-traitement des sorties de E2-E3, E5 et E9 ensuite, E7 en dernier.")]));

// 6 grille
children.push(H1("6. Grille de lecture des résultats"));
children.push(table(
  ["Observation après E1-E4", "Interprétation", "Conséquence pour la suite"],
  [
    ["Aérien interne : côté relatif p50 < 2 % et gain de tuilage ≥ 20 points de rappel", "H1 et H4 confirmées : l'écart 90 → 58 est surtout une convention d'échelle", "Fixer la convention d'évaluation tuilée ; ré-évaluer le 58 % ; priorité au tuilage et à la résolution avant toute adaptation de domaine"],
    ["Aérien interne : côté relatif p50 ≥ 4 % et gain de tuilage < 5 points", "H1 infirmée, H5 confirmée : vrai décalage d'apparence", "Programme d'adaptation de domaine ou de pré-entraînement aérien ; conserver la convention actuelle"],
    ["Gain de tuilage intermédiaire (5-20 points) et perte résiduelle 10-25 points", "Cas mixte, le plus probable a priori", "Les deux chantiers, dans cet ordre : tuilage puis adaptation"],
    ["FP/image ≥ 1 à 80 % de rappel (E6)", "H6 confirmée : le fond marin vu du dessus est le problème n° 1 de précision", "Ajouter des négatifs aériens (images vides) à l'entraînement suivant ; filtrage par contexte"],
    ["AP@0,3 − AP@0,5 ≥ 10 points en aérien (E3)", "H11 confirmée : une part de l'écart est métrique", "Rapporter systématiquement AP@0,3 et NWD à côté de AP@0,5 pour les objets < 15 px"],
    ["RT-DETRv2 apparié < Grounding DINO zero-shot (E9)", "H9 : le pré-entraînement sous-marin n'apporte rien en aérien", "Repartir d'un modèle ouvert ou d'un pré-entraînement aérien pour la phase d'entraînement"],
    ["IoU inter-annotateurs < 0,7 ou > 10 % de boîtes hors cadre (E1, H12)", "Les annotations internes ne permettent pas de conclure", "Ré-annoter avant toute autre expérience"],
  ], [3300, 3000, 3300]));
children.push(gap());

// 7 limites
children.push(H1("7. Limites et points à vérifier"));
children.push(B("Les métriques internes (« 90 % », « 58 % ») n'ont pas été définies dans les documents disponibles ; toutes les prédictions supposent une AP@0,5 ou un F1 et doivent être reformulées si la métrique diffère."));
children.push(B("Les chiffres de Chen et al. 2018 sont rapportés d'après un article secondaire [21] et ceux de Green et al. 2023 sont incomplets (précision et rappel non accessibles) : à vérifier sur les textes intégraux."));
children.push(B("Les jeux publics ne contiennent pas de mégafaune sous-marine annotée en boîtes : la référence sous-marine repose sur des poissons (NOAA, jeu communautaire), dont les conventions peuvent différer des données internes."));
children.push(B("Aucune étude publiée ne teste directement un transfert sous-marin → aérien ; les intervalles de H5 et H9 sont extrapolés de transferts aérien → satellite [6], de benchmarks open-world [19] et d'adaptation de domaine au sol [21]."));
children.push(B("Les gains de tuilage publiés [3][26] concernent des détecteurs entraînés dans le domaine cible ; appliqués à un modèle sous-marin non adapté, ils constituent une borne haute."));

// 8 refs
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(H1("8. Références"));
refs.forEach((r, i) => children.push(new Paragraph({ spacing: { after: 80 }, indent: { left: 500, hanging: 500 }, children: [new TextRun({ text: `[${i + 1}] `, font: FONT, size: 20, bold: true }), new TextRun({ text: r, font: FONT, size: 20 })] })));

const doc = new Document({
  creator: "GoldenEye / SogetiLabs", title: "Hypothèses a priori — généralisation cross-domaine RT-DETRv2",
  styles: {
    default: { document: { run: { font: FONT, size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, color: "1F4E79", font: FONT }, paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 26, bold: true, color: "2E75B6", font: FONT }, paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 23, bold: true, font: FONT }, paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }, { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 1440, hanging: 360 } } } }] },
    { reference: "nums", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ] },
  features: { updateFields: true },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1250, bottom: 1250, left: 1300, right: 1300 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "GoldenEye — Hypothèses a priori cross-domaine — v1.0", font: FONT, size: 16, color: "808080" })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Page ", font: FONT, size: 16, color: "808080" }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: "808080" })] })] }) },
    children,
  }],
});
Packer.toBuffer(doc).then(buf => { fs.writeFileSync(process.argv[2], buf); console.log("ok", buf.length); });
