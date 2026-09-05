
from __future__ import annotations
from typing import Any

DEVELOPMENT_MAPPING_NOTICE = (
    "Synthetic development mapping only. Not a prescribing protocol, "
    "not a dosing guide, and not actual health-center utilization."
)

def med(
    key: str,
    label: str,
    names: list[str],
    strengths: list[str] | None = None,
    forms: list[str] | None = None,
    probability: float = 0.5,
    quantity_range: tuple[int, int] = (1, 8),
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "name_aliases": set(names),
        "strength_aliases": set(strengths or []),
        "form_aliases": set(forms or []),
        "selection_probability": probability,
        "quantity_range": quantity_range,
    }

def rule(
    key: str,
    codes: list[str],
    names: list[str],
    group: str,
    medicines: list[dict[str, Any]],
    sensitive: bool = False,
) -> dict[str, Any]:
    return {
        "key": key,
        "codes": set(codes),
        "names": {name.lower() for name in names},
        "group": group,
        "sensitive": sensitive,
        "medicines": medicines,
    }

# Artificial inventory-demand quantities below are NOT patient doses.
DISEASE_MEDICINE_RULES = [
    rule("DENGUE", ["DENGUE","DENG"], ["Dengue"], "COMMUNICABLE", [
        med("PARA500","Paracetamol 500 mg Tablet",["Paracetamol"],["500 mg"],["Tablet"],0.80,(2,12)),
        med("ORS","Oral Rehydration Salts Sachet",["Oral Rehydration Salts","ORS"],None,["Sachet","Powder"],0.45,(1,5)),
    ]),
    rule("ARI", ["ARI"], ["Acute Respiratory Infection","Acute Respiratory Infection (ARI)"], "COMMUNICABLE", [
        med("PARA500","Paracetamol 500 mg Tablet",["Paracetamol"],["500 mg"],["Tablet"],0.55,(2,12)),
        med("CET10","Cetirizine 10 mg Tablet",["Cetirizine"],["10 mg"],["Tablet"],0.35,(2,10)),
        med("SALBNEB","Salbutamol Nebule",["Salbutamol","Salbutamol Sulfate"],None,["Nebule"],0.28,(1,6)),
        med("ASC500","Ascorbic Acid 500 mg Tablet",["Ascorbic Acid"],["500 mg"],["Tablet"],0.38,(2,12)),
        med("LAGUNDI","Lagundi / Vitex Negundo",["Lagundi","Lagundi Leaf","Vitex Negundo"],None,None,0.30,(1,8)),
    ]),
    rule("ILI", ["ILI"], ["Influenza-Like Illness","Influenza-Like Illness (ILI)"], "COMMUNICABLE", [
        med("PARA500","Paracetamol 500 mg Tablet",["Paracetamol"],["500 mg"],["Tablet"],0.70,(2,12)),
        med("ASC500","Ascorbic Acid 500 mg Tablet",["Ascorbic Acid"],["500 mg"],["Tablet"],0.45,(2,12)),
        med("CET10","Cetirizine 10 mg Tablet",["Cetirizine"],["10 mg"],["Tablet"],0.25,(2,10)),
        med("ORS","Oral Rehydration Salts Sachet",["Oral Rehydration Salts","ORS"],None,["Sachet","Powder"],0.20,(1,4)),
        med("OSELT75","Oseltamivir 75 mg Capsule",["Oseltamivir"],["75 mg"],["Capsule"],0.08,(1,6)),
    ]),
    rule("GE", ["DIARRHEA_GASTROENTERITIS","GE"], ["Diarrhea / Gastroenteritis","Gastroenteritis"], "COMMUNICABLE", [
        med("ORS","Oral Rehydration Salts Sachet",["Oral Rehydration Salts","ORS"],None,["Sachet","Powder"],0.85,(1,6)),
        med("ZINC20","Zinc 20 mg Tablet",["Zinc","Zinc Sulfate"],["20 mg"],["Tablet","Dispersible Tablet"],0.40,(2,10)),
        med("METRO500","Metronidazole 500 mg Tablet",["Metronidazole"],["500 mg"],["Tablet"],0.12,(2,10)),
    ]),

    rule("HTN", ["HTN","HYPERTENSION"], ["Hypertension"], "NON_COMMUNICABLE", [
        med("AMLO5","Amlodipine 5 mg Tablet",["Amlodipine"],["5 mg"],["Tablet"],0.55,(5,20)),
        med("LOS50","Losartan 50 mg Tablet",["Losartan"],["50 mg"],["Tablet"],0.35,(5,20)),
        med("TEL40","Telmisartan 40 mg Tablet",["Telmisartan"],["40 mg"],["Tablet"],0.18,(5,20)),
    ]),
    rule("T2DM", ["T2DM","TYPE_2_DIABETES"], ["Type 2 Diabetes Mellitus"], "NON_COMMUNICABLE", [
        med("MET500","Metformin 500 mg Tablet",["Metformin"],["500 mg"],["Tablet"],0.70,(5,24)),
        med("GLIC30","Gliclazide 30 mg Tablet",["Gliclazide"],["30 mg"],["Tablet","MR Tablet","Modified Release Tablet"],0.42,(5,20)),
        med("DAPA10","Dapagliflozin 10 mg Tablet",["Dapagliflozin"],["10 mg"],["Tablet"],0.15,(5,20)),
    ]),
    rule("DYS", ["DYSLIPIDEMIA","DYS"], ["Dyslipidemia"], "NON_COMMUNICABLE", [
        med("ATOR20","Atorvastatin 20 mg Tablet",["Atorvastatin"],["20 mg"],["Tablet"],0.60,(5,20)),
        med("SIMVA20","Simvastatin 20 mg Tablet",["Simvastatin"],["20 mg"],["Tablet"],0.25,(5,20)),
        med("ROSU20","Rosuvastatin 20 mg Tablet",["Rosuvastatin"],["20 mg"],["Tablet"],0.15,(5,20)),
    ]),
    rule("ASTHMA", ["ASTHMA"], ["Asthma"], "RESPIRATORY", [
        med("SALBNEB","Salbutamol Nebule",["Salbutamol","Salbutamol Sulfate"],None,["Nebule"],0.75,(1,8)),
        med("MONT10","Montelukast 10 mg Tablet",["Montelukast"],["10 mg"],["Tablet"],0.25,(2,12)),
        med("BUDFORM","Budesonide + Formoterol Inhaler",["Budesonide + Formoterol","Budesonide/Formoterol"],None,["MDI","Inhaler"],0.15,(1,2)),
    ]),
    rule("COPD", ["COPD"], ["Chronic Obstructive Pulmonary Disease","COPD"], "RESPIRATORY", [
        med("IPRA","Ipratropium Nebule",["Ipratropium"],None,["Nebule"],0.55,(1,8)),
        med("SALBNEB","Salbutamol Nebule",["Salbutamol","Salbutamol Sulfate"],None,["Nebule"],0.55,(1,8)),
        med("TIO","Tiotropium Inhalation",["Tiotropium"],None,["Inhalation Capsule","DPI"],0.18,(1,6)),
    ]),
    rule("UTI", ["UTI"], ["Urinary Tract Infection","Urinary Tract Infection (UTI)"], "OTHER_CONDITION", [
        med("NITRO100","Nitrofurantoin 100 mg Capsule",["Nitrofurantoin"],["100 mg"],["Capsule"],0.45,(2,10)),
        med("CEFIX200","Cefixime 200 mg Capsule",["Cefixime"],["200 mg"],["Capsule"],0.20,(2,10)),
    ]),
    rule("PNEUMONIA", ["PNEUMONIA","BACTERIAL_RESPIRATORY_INFECTION"], ["Pneumonia / Bacterial Respiratory Infection","Pneumonia"], "RESPIRATORY", [
        med("AMOX500","Amoxicillin 500 mg Capsule",["Amoxicillin"],["500 mg"],["Capsule"],0.50,(2,12)),
        med("AZI500","Azithromycin 500 mg Tablet",["Azithromycin"],["500 mg"],["Tablet"],0.20,(1,8)),
        med("CEFU500","Cefuroxime 500 mg Tablet",["Cefuroxime"],["500 mg"],["Tablet"],0.18,(2,10)),
    ]),
    rule("HELM", ["HELMINTHIASIS"], ["Helminthiasis","Intestinal Helminthiasis"], "OTHER_CONDITION", [
        med("ALB400","Albendazole 400 mg Chewable Tablet",["Albendazole"],["400 mg"],["Chewable Tablet","Tablet"],0.70,(1,4)),
        med("MEB500","Mebendazole 500 mg Chewable Tablet",["Mebendazole"],["500 mg"],["Chewable Tablet","Tablet"],0.30,(1,4)),
    ]),
    rule("FUNGAL", ["FUNGAL_INFECTION","CANDIDIASIS"], ["Fungal Infection / Candidiasis","Candidiasis","Fungal Infection"], "OTHER_CONDITION", [
        med("CLOT1","Clotrimazole 1% Cream",["Clotrimazole"],["1%"],["Cream"],0.65,(1,3)),
        med("FLUC150","Fluconazole 150 mg Capsule",["Fluconazole"],["150 mg"],["Capsule"],0.25,(1,4)),
    ]),
    rule("GERD", ["GERD_DYSPEPSIA","GERD"], ["GERD / Dyspepsia","Gastroesophageal Reflux Disease","Dyspepsia"], "OTHER_CONDITION", [
        med("OME20","Omeprazole 20 mg Capsule",["Omeprazole"],["20 mg"],["Capsule"],0.65,(2,14)),
        med("ANTACID","Aluminum Hydroxide + Magnesium Hydroxide",["Aluminum Hydroxide + Magnesium Hydroxide"],None,None,0.35,(2,12)),
    ]),
    rule("GOUT", ["GOUT"], ["Gout"], "OTHER_CONDITION", [
        med("COL500","Colchicine 500 mcg Tablet",["Colchicine"],["500 mcg","0.5 mg"],["Tablet"],0.60,(1,8)),
        med("NAP500","Naproxen 500 mg Tablet",["Naproxen"],["500 mg"],["Tablet"],0.28,(2,10)),
    ]),
    rule("IDA", ["IRON_DEF_ANEMIA","IDA"], ["Iron Deficiency Anemia"], "OTHER_CONDITION", [
        med("FERROUS","Ferrous Salt / Ferrous Sulfate",["Ferrous Salt","Ferrous Sulfate"],None,["Tablet"],0.75,(5,20)),
        med("FERROUS_FOLIC","Ferrous Salt + Folic Acid",["Ferrous Salt + Folic Acid","Ferrous Sulfate + Folic Acid"],None,["Tablet"],0.30,(5,20)),
    ]),
    rule("ARH", ["ALLERGIC_RHINITIS","ARH"], ["Allergic Rhinitis"], "OTHER_CONDITION", [
        med("CET10","Cetirizine 10 mg Tablet",["Cetirizine"],["10 mg"],["Tablet"],0.65,(2,12)),
        med("LORA10","Loratadine 10 mg Tablet",["Loratadine"],["10 mg"],["Tablet"],0.35,(2,12)),
    ]),
    rule("IHD", ["IHD_ANGINA","IHD","ANGINA"], ["Ischemic Heart Disease / Angina","Ischemic Heart Disease","Angina"], "CARDIOVASCULAR", [
        med("ASA80","Aspirin 80 mg Tablet",["Aspirin"],["80 mg"],["Tablet"],0.50,(5,20)),
        med("CLOP75","Clopidogrel 75 mg Tablet",["Clopidogrel"],["75 mg"],["Tablet"],0.35,(5,20)),
        med("ISOS","Isosorbide Formulation",["Isosorbide Dinitrate","Isosorbide Mononitrate"],None,None,0.22,(2,12)),
    ]),

    rule("TB", ["TB","TUBERCULOSIS","PTB"], ["Tuberculosis","Pulmonary Tuberculosis"], "SENSITIVE_PROGRAM", [
        med("TB4FDC","TB 4-drug Fixed-Dose Combination",["Rifampicin + Isoniazid + Pyrazinamide + Ethambutol"],None,["Tablet"],0.70,(4,18)),
        med("TB2FDC","Rifampicin + Isoniazid Fixed-Dose Combination",["Rifampicin + Isoniazid"],None,["Tablet"],0.40,(4,18)),
        med("INH","Isoniazid Tablet",["Isoniazid"],None,["Tablet"],0.20,(4,18)),
    ], True),
    rule("HIV", ["HIV"], ["HIV","HIV Infection"], "SENSITIVE_PROGRAM", [
        med("TLD","Tenofovir + Lamivudine + Dolutegravir",["Tenofovir + Lamivudine + Dolutegravir","TDF + Lamivudine + Dolutegravir"],None,["Tablet"],0.75,(4,18)),
        med("DTG","Dolutegravir Tablet",["Dolutegravir"],None,["Tablet"],0.20,(4,18)),
    ], True),
    rule("SYPH", ["SYPH","SYPHILIS"], ["Syphilis"], "SENSITIVE_PROGRAM", [
        med("BPG","Benzathine Penicillin G Injection",["Benzathine Penicillin G"],None,["Injection","Vial"],0.70,(1,2)),
    ], True),
    rule("GC", ["GONORRHEA","GC"], ["Gonorrhea","Gonorrhoea"], "SENSITIVE_PROGRAM", [
        med("CTX","Ceftriaxone Injection",["Ceftriaxone"],None,["Injection","Vial"],0.70,(1,2)),
    ], True),
    rule("HSV", ["HSV","HSV_GENITAL","GENITAL_HERPES"], ["Genital Herpes","Genital Herpes Simplex"], "SENSITIVE_PROGRAM", [
        med("ACY800","Acyclovir 800 mg Tablet",["Acyclovir"],["800 mg"],["Tablet"],0.65,(2,12)),
    ], True),
]

def get_mapping_rule(*, disease_code: str | None, disease_name: str | None):
    code = str(disease_code or "").strip().upper()
    name = str(disease_name or "").strip().lower()
    for item in DISEASE_MEDICINE_RULES:
        codes = {str(value).strip().upper() for value in item["codes"]}
        names = {str(value).strip().lower() for value in item["names"]}
        if code in codes or name in names:
            return item
    return None
