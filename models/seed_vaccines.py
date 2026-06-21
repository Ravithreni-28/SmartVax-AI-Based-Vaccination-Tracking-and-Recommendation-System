from models.models import Vaccine
from extensions import db
from datetime import datetime


VACCINE_DATA = [
    # Birth
    {"vaccine_name": "BCG (Tuberculosis)", "recommended_age_months": 0, "dose_number": 1,
     "description": "Protects against tuberculosis. Given at birth.", "disease_prevented": "Tuberculosis", "category": "Mandatory"},
    {"vaccine_name": "Hepatitis B (Dose 1)", "recommended_age_months": 0, "dose_number": 1,
     "description": "First dose of Hepatitis B vaccine. Given at birth.", "disease_prevented": "Hepatitis B", "category": "Mandatory"},
    {"vaccine_name": "OPV (Dose 0)", "recommended_age_months": 0, "dose_number": 0,
     "description": "Oral Polio Vaccine given at birth.", "disease_prevented": "Poliomyelitis", "category": "Mandatory"},

    # 6 weeks
    {"vaccine_name": "DPT (Dose 1)", "recommended_age_months": 2, "dose_number": 1,
     "description": "Diphtheria, Pertussis (Whooping Cough), Tetanus vaccine.", "disease_prevented": "Diphtheria, Pertussis, Tetanus", "category": "Mandatory"},
    {"vaccine_name": "Hepatitis B (Dose 2)", "recommended_age_months": 2, "dose_number": 2,
     "description": "Second dose of Hepatitis B vaccine.", "disease_prevented": "Hepatitis B", "category": "Mandatory"},
    {"vaccine_name": "OPV (Dose 1)", "recommended_age_months": 2, "dose_number": 1,
     "description": "Oral Polio Vaccine first scheduled dose.", "disease_prevented": "Poliomyelitis", "category": "Mandatory"},
    {"vaccine_name": "Rotavirus (Dose 1)", "recommended_age_months": 2, "dose_number": 1,
     "description": "Protects against rotavirus gastroenteritis.", "disease_prevented": "Rotavirus Diarrhea", "category": "Recommended"},
    {"vaccine_name": "PCV (Dose 1)", "recommended_age_months": 2, "dose_number": 1,
     "description": "Pneumococcal Conjugate Vaccine.", "disease_prevented": "Pneumococcal Disease", "category": "Recommended"},

    # 10 weeks
    {"vaccine_name": "DPT (Dose 2)", "recommended_age_months": 3, "dose_number": 2,
     "description": "Second dose of DPT vaccine.", "disease_prevented": "Diphtheria, Pertussis, Tetanus", "category": "Mandatory"},
    {"vaccine_name": "OPV (Dose 2)", "recommended_age_months": 3, "dose_number": 2,
     "description": "Second dose of Oral Polio Vaccine.", "disease_prevented": "Poliomyelitis", "category": "Mandatory"},
    {"vaccine_name": "Rotavirus (Dose 2)", "recommended_age_months": 3, "dose_number": 2,
     "description": "Second dose of Rotavirus Vaccine.", "disease_prevented": "Rotavirus Diarrhea", "category": "Recommended"},

    # 14 weeks
    {"vaccine_name": "DPT (Dose 3)", "recommended_age_months": 4, "dose_number": 3,
     "description": "Third dose of DPT vaccine.", "disease_prevented": "Diphtheria, Pertussis, Tetanus", "category": "Mandatory"},
    {"vaccine_name": "OPV (Dose 3)", "recommended_age_months": 4, "dose_number": 3,
     "description": "Third dose of Oral Polio Vaccine.", "disease_prevented": "Poliomyelitis", "category": "Mandatory"},
    {"vaccine_name": "Hepatitis B (Dose 3)", "recommended_age_months": 4, "dose_number": 3,
     "description": "Third dose of Hepatitis B vaccine.", "disease_prevented": "Hepatitis B", "category": "Mandatory"},
    {"vaccine_name": "PCV (Dose 2)", "recommended_age_months": 4, "dose_number": 2,
     "description": "Second dose of Pneumococcal Vaccine.", "disease_prevented": "Pneumococcal Disease", "category": "Recommended"},

    # 6 months
    {"vaccine_name": "Influenza (Dose 1)", "recommended_age_months": 6, "dose_number": 1,
     "description": "Annual flu vaccine for children.", "disease_prevented": "Influenza", "category": "Recommended"},
    {"vaccine_name": "Hepatitis B (Dose 4)", "recommended_age_months": 6, "dose_number": 4,
     "description": "Booster dose of Hepatitis B.", "disease_prevented": "Hepatitis B", "category": "Mandatory"},

    # 9 months
    {"vaccine_name": "MMR (Dose 1)", "recommended_age_months": 9, "dose_number": 1,
     "description": "Measles, Mumps, and Rubella combined vaccine.", "disease_prevented": "Measles, Mumps, Rubella", "category": "Mandatory"},
    {"vaccine_name": "Vitamin A (Dose 1)", "recommended_age_months": 9, "dose_number": 1,
     "description": "Vitamin A supplementation to prevent deficiency.", "disease_prevented": "Vitamin A Deficiency", "category": "Recommended"},

    # 12 months
    {"vaccine_name": "PCV (Dose 3)", "recommended_age_months": 12, "dose_number": 3,
     "description": "Booster dose of Pneumococcal Vaccine.", "disease_prevented": "Pneumococcal Disease", "category": "Recommended"},
    {"vaccine_name": "Varicella (Dose 1)", "recommended_age_months": 12, "dose_number": 1,
     "description": "Chickenpox vaccine first dose.", "disease_prevented": "Varicella (Chickenpox)", "category": "Recommended"},
    {"vaccine_name": "Hepatitis A (Dose 1)", "recommended_age_months": 12, "dose_number": 1,
     "description": "Hepatitis A first dose.", "disease_prevented": "Hepatitis A", "category": "Recommended"},

    # 15 months
    {"vaccine_name": "MMR (Dose 2)", "recommended_age_months": 15, "dose_number": 2,
     "description": "Second dose of MMR vaccine.", "disease_prevented": "Measles, Mumps, Rubella", "category": "Mandatory"},

    # 18 months
    {"vaccine_name": "DPT Booster (Dose 1)", "recommended_age_months": 18, "dose_number": 4,
     "description": "Booster dose of DPT at 18 months.", "disease_prevented": "Diphtheria, Pertussis, Tetanus", "category": "Mandatory"},
    {"vaccine_name": "OPV Booster", "recommended_age_months": 18, "dose_number": 4,
     "description": "Booster dose of Oral Polio Vaccine.", "disease_prevented": "Poliomyelitis", "category": "Mandatory"},
    {"vaccine_name": "Hepatitis A (Dose 2)", "recommended_age_months": 18, "dose_number": 2,
     "description": "Second dose of Hepatitis A vaccine.", "disease_prevented": "Hepatitis A", "category": "Recommended"},
    {"vaccine_name": "Varicella (Dose 2)", "recommended_age_months": 18, "dose_number": 2,
     "description": "Second dose of Chickenpox vaccine.", "disease_prevented": "Varicella (Chickenpox)", "category": "Recommended"},

    # 2 years
    {"vaccine_name": "Typhoid Conjugate Vaccine", "recommended_age_months": 24, "dose_number": 1,
     "description": "Typhoid Conjugate Vaccine for children.", "disease_prevented": "Typhoid", "category": "Recommended"},

    # 4-6 years
    {"vaccine_name": "DTaP Booster (Pre-School)", "recommended_age_months": 48, "dose_number": 5,
     "description": "Pre-school booster of DTaP vaccine.", "disease_prevented": "Diphtheria, Pertussis, Tetanus", "category": "Mandatory"},
    {"vaccine_name": "IPV Booster (Pre-School)", "recommended_age_months": 48, "dose_number": 5,
     "description": "Inactivated Polio Vaccine booster before school.", "disease_prevented": "Poliomyelitis", "category": "Mandatory"},
    {"vaccine_name": "MMR (Dose 3)", "recommended_age_months": 60, "dose_number": 3,
     "description": "Third MMR dose given at school entry.", "disease_prevented": "Measles, Mumps, Rubella", "category": "Mandatory"},

    # 10-12 years
    {"vaccine_name": "HPV (Dose 1)", "recommended_age_months": 120, "dose_number": 1,
     "description": "Human Papillomavirus vaccine for adolescents.", "disease_prevented": "HPV-related Cancers", "category": "Recommended"},
    {"vaccine_name": "Tdap Booster", "recommended_age_months": 132, "dose_number": 6,
     "description": "Tetanus, Diphtheria, Pertussis booster for adolescents.", "disease_prevented": "Tetanus, Diphtheria, Pertussis", "category": "Mandatory"},

    # 16-18 years
    {"vaccine_name": "HPV (Dose 2)", "recommended_age_months": 144, "dose_number": 2,
     "description": "Second dose of HPV vaccine.", "disease_prevented": "HPV-related Cancers", "category": "Recommended"},
    {"vaccine_name": "Meningococcal Vaccine", "recommended_age_months": 144, "dose_number": 1,
     "description": "Protects against bacterial meningitis.", "disease_prevented": "Meningococcal Disease", "category": "Recommended"},

    # Adults (18+ years = 216 months)
    {"vaccine_name": "Influenza (Annual)", "recommended_age_months": 216, "dose_number": 1,
     "description": "Annual influenza vaccination for adults.", "disease_prevented": "Influenza", "category": "Recommended"},
    {"vaccine_name": "Hepatitis B (Adult)", "recommended_age_months": 216, "dose_number": 1,
     "description": "Hepatitis B catch-up for unvaccinated adults.", "disease_prevented": "Hepatitis B", "category": "Recommended"},
    {"vaccine_name": "COVID-19 Vaccine", "recommended_age_months": 216, "dose_number": 1,
     "description": "COVID-19 primary series vaccination.", "disease_prevented": "COVID-19", "category": "Recommended"},
    {"vaccine_name": "Td Booster (Adult)", "recommended_age_months": 240, "dose_number": 7,
     "description": "Adult Tetanus-Diphtheria booster every 10 years.", "disease_prevented": "Tetanus, Diphtheria", "category": "Mandatory"},
]


def seed_vaccines(app):
    with app.app_context():
        if Vaccine.query.count() == 0:
            for v_data in VACCINE_DATA:
                vaccine = Vaccine(**v_data)
                db.session.add(vaccine)
            db.session.commit()
            print(f"[OK] Seeded {len(VACCINE_DATA)} vaccines to database.")
        else:
            print("[INFO] Vaccines already seeded.")
