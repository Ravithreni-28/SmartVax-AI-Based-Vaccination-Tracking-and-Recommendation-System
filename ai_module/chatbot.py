import re
import random
from datetime import datetime


# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
#  COMPREHENSIVE VACCINE KNOWLEDGE BASE
# ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ── ──
INTENTS = {

    # ── GREETINGS & HELP ──────────────────────────────────────────────────
    "greeting": {
        "patterns": ["hello", "hi", "hey", "good morning", "good afternoon",
                     "good evening", "howdy", "greetings", "what's up", "sup",
                     "hii", "helo", "helo there"],
        "responses": [
            "👋 Hello! I'm SmartVax AI — your personal vaccine expert. Ask me anything about vaccines, diseases, schedules, or immunity!",
            "Hi there! 😊 I can answer questions about vaccines, diseases they prevent, causes, symptoms, side effects, and much more. What would you like to know?",
            "Hey! Welcome to SmartVax Assistant. I have detailed knowledge on 30+ vaccines and the diseases they prevent. How can I help today?"
        ],
        "suggestions": ["What is vaccination?", "Show me the vaccine schedule", "What are side effects?"]
    },
    "chatbot_help": {
        "patterns": ["help", "what can you do", "what do you know", "how to use",
                     "what can i ask", "topics", "capabilities", "guide me"],
        "responses": [
            "🤖 I can answer questions about:\n• **What vaccines are** and how they work\n• **Diseases** — causes, symptoms, prevention\n• **Specific vaccines** — BCG, MMR, OPV, DPT, COVID-19, HPV, etc.\n• **Vaccine schedules** — when to get vaccinated\n• **Side effects** and safety\n• **Missed doses** and catch-up strategies\n• **Herd immunity**, ingredients, vaccine types\n\nJust ask me anything! 💉"
        ],
        "suggestions": ["Vaccine schedule", "BCG vaccine", "What is herd immunity?"]
    },
    "farewell": {
        "patterns": ["bye", "goodbye", "see you", "thank you", "thanks", "cya",
                     "take care", "tata", "ok bye", "that's all"],
        "responses": [
            "👋 Goodbye! Stay vaccinated and stay protected! 💙",
            "Thanks for using SmartVax! Remember — vaccines save lives. Take care! 🌟",
            "Stay healthy! Check your SmartVax dashboard for your next upcoming vaccine. Bye! 😊"
        ],
        "suggestions": ["Check my schedule", "View reminders"]
    },

    # ── WHAT IS VACCINATION ───────────────────────────────────────────────
    "what_is_vaccination": {
        "patterns": ["what is vaccination", "what is a vaccine", "define vaccine",
                     "explain vaccination", "meaning of vaccine", "what does vaccine mean",
                     "what is immunization", "vaccination meaning", "what are vaccines",
                     "vaccine definition", "define immunization"],
        "responses": [
            "💉 **What is Vaccination?**\n\nVaccination is the process of introducing a weakened or inactivated form of a pathogen — or its proteins — into the body to stimulate the immune system to produce antibodies.\n\n✅ **Result:** Your immune system 'remembers' the pathogen. If you encounter the real disease later, your body fights it off quickly.\n\nVaccines are one of the greatest public health achievements — they eradicated smallpox and nearly eliminated polio worldwide!",
            "🛡️ **Vaccination Explained:**\n\nA vaccine trains your immune system to recognize and fight specific diseases **without causing the disease itself**.\n\n**How it works:**\n1️⃣ Vaccine introduces an antigen (harmless piece of pathogen)\n2️⃣ Immune system detects it and produces antibodies\n3️⃣ Memory cells are created\n4️⃣ Future exposure → rapid immune response → you stay protected!"
        ],
        "suggestions": ["How do vaccines work?", "Types of vaccines", "Why vaccinate?"]
    },
    "how_vaccines_work": {
        "patterns": ["how do vaccines work", "how does vaccination work", "mechanism of vaccine",
                     "how does a vaccine protect", "how does immunity develop",
                     "science behind vaccines", "vaccine mechanism", "how vaccines protect us"],
        "responses": [
            "🔬 **How Vaccines Work:**\n\nWhen a vaccine enters your body:\n\n1. **Antigen Recognition** — Your immune system identifies the foreign antigen\n2. **Antibody Production** — B-cells produce antibodies that target that pathogen\n3. **Memory Formation** — Memory B and T cells 'remember' the pathogen for years\n4. **Future Protection** — Real pathogen encountered later → memory cells mount rapid defense!\n\nThis is called **acquired immunity**. It's safe, effective, and long-lasting! 🌟"
        ],
        "suggestions": ["Types of vaccines", "What is herd immunity?", "Vaccine safety"]
    },
    "types_of_vaccines": {
        "patterns": ["types of vaccines", "kinds of vaccines", "vaccine types",
                     "live attenuated", "inactivated vaccine", "mrna vaccine",
                     "subunit vaccine", "different vaccines", "categories of vaccines"],
        "responses": [
            "🧬 **Types of Vaccines:**\n\n1. **Live-Attenuated** — Weakened live pathogen (MMR, Varicella, OPV). Strongest immunity.\n\n2. **Inactivated** — Killed pathogen (IPV, Hepatitis A, Flu shot). Safe for everyone.\n\n3. **Subunit/Protein** — Only specific proteins from the pathogen (Hepatitis B, HPV, Pertussis). Very safe.\n\n4. **mRNA** — Genetic instructions to make a protein (COVID-19 Pfizer/Moderna). No live virus, cannot alter DNA.\n\n5. **Viral Vector** — Modified virus to deliver instructions (COVID-19 AstraZeneca).\n\n6. **Toxoid** — Inactivated toxin (Tetanus, Diphtheria). Protects against toxin."
        ],
        "suggestions": ["mRNA vaccine safety", "COVID-19 vaccine", "What is BCG?"]
    },
    "importance_of_vaccines": {
        "patterns": ["why vaccinate", "why are vaccines important", "importance of vaccination",
                     "benefits of vaccination", "why should i get vaccinated", "need for vaccination",
                     "purpose of vaccination", "why do we need vaccines", "why vaccines matter"],
        "responses": [
            "🌍 **Why Vaccination is Important:**\n\n✅ **Personal Protection** — Prevents serious, life-threatening diseases\n✅ **Family Protection** — Protects those around you (babies, elderly, immunocompromised)\n✅ **Herd Immunity** — When enough people are vaccinated, diseases can't spread easily\n✅ **Disease Eradication** — Vaccines eradicated smallpox and nearly eliminated polio\n✅ **Economic Benefits** — Prevents hospitalizations, saving billions in costs\n✅ **Safe & Tested** — Every vaccine undergoes rigorous clinical trials before approval\n\n💡 **Fact:** Vaccines save 2–3 million lives every year globally!"
        ],
        "suggestions": ["What is herd immunity?", "Vaccine safety facts", "Vaccine schedule"]
    },
    "herd_immunity": {
        "patterns": ["herd immunity", "community immunity", "herd protection",
                     "what is herd immunity", "how herd immunity works", "population immunity"],
        "responses": [
            "🌐 **Herd Immunity:**\n\nWhen a large portion of a population is immune (through vaccination or past infection), the spread of disease slows — protecting even those who can't be vaccinated.\n\n📊 **Herd immunity thresholds:**\n• Measles: ~95% vaccination rate needed\n• Polio: ~80–85%\n• COVID-19: ~70–80%\n• Flu: ~33–44%\n\nThis is why community vaccination matters — you protect others too! 💙"
        ],
        "suggestions": ["Why vaccinate?", "MMR vaccine", "COVID-19 vaccine"]
    },
    "vaccine_ingredients": {
        "patterns": ["vaccine ingredients", "what is in vaccines", "vaccine components",
                     "adjuvants", "preservatives in vaccine", "vaccine contents", "thimerosal",
                     "aluminum in vaccines", "what vaccines are made of"],
        "responses": [
            "🧪 **What's in Vaccines?**\n\n• **Antigens** — The key ingredient: killed/weakened pathogen or its proteins\n• **Adjuvants** (e.g., aluminum salts) — Boost immune response; found in tiny, safe amounts\n• **Stabilizers** (sugars, gelatin) — Keep the vaccine effective during storage\n• **Preservatives** (thimerosal in multi-dose vials) — Prevent contamination; mercury amount is less than in a tuna sandwich\n• **Diluents** (saline/water) — For reconstitution\n\n✅ Every ingredient is tested for safety. Vaccines contain NO live harmful pathogens in killed-virus types."
        ],
        "suggestions": ["Are vaccines safe?", "Side effects", "HPV vaccine"]
    },

    # ── SIDE EFFECTS & SAFETY ─────────────────────────────────────────────
    "side_effects": {
        "patterns": ["side effects", "vaccine reaction", "after vaccine", "vaccine fever",
                     "sore arm", "common side effects", "adverse effects", "vaccine pain",
                     "swelling after vaccine", "redness after vaccine", "vaccine symptoms"],
        "responses": [
            "💊 **Common Vaccine Side Effects** (Normal & Temporary):\n\n• 🔴 Soreness, redness, swelling at injection site\n• 🌡️ Low-grade fever (37.5–38.5°C)\n• 😴 Fatigue or tiredness\n• 🤕 Mild headache or muscle aches\n• 🤢 Nausea (rare)\n\nThese are **signs your immune system is responding** — not harm!\n\n⏰ Side effects usually resolve in **1–3 days**.\n\n🚨 **Serious reactions are extremely rare** (~1–2 per million doses). Contact a doctor if you experience difficulty breathing or swelling of face/throat."
        ],
        "suggestions": ["Are vaccines safe?", "What is anaphylaxis?", "Missed dose guidance"]
    },
    "vaccine_safety": {
        "patterns": ["are vaccines safe", "vaccine safe", "is vaccination safe", "vaccine myth",
                     "vaccine facts", "anti vaccine", "vaccines cause autism", "vaccine conspiracy",
                     "vaccine dangers", "is mmr safe", "are vaccines harmful"],
        "responses": [
            "✅ **Vaccines Are Safe — Here's the Evidence:**\n\nEvery vaccine goes through:\n1️⃣ **Preclinical testing** (animals)\n2️⃣ **Phase I, II, III clinical trials** (thousands of humans)\n3️⃣ **Regulatory review** (FDA, WHO, EMA approval)\n4️⃣ **Post-market surveillance** (ongoing monitoring after approval)\n\n🔬 **On the autism myth:** The 1998 Wakefield study claiming MMR causes autism was **fraudulent, retracted, and debunked** by dozens of large-scale studies involving millions of children. The author lost his medical license.\n\n💡 The benefits vastly outweigh the tiny risk of side effects. Not vaccinating is a far greater risk.",
            "🌟 **Vaccine Safety Facts:**\n\n• Vaccines are monitored by WHO, CDC, and national health agencies\n• Serious adverse events are extremely rare (~1–2 per million doses)\n• Not vaccinating carries far greater risks — measles can cause brain damage, polio can paralyze\n• 2–3 million lives are saved by vaccines every year\n• Smallpox has been completely eradicated thanks to vaccines"
        ],
        "suggestions": ["Side effects explained", "How vaccines work", "Herd immunity"]
    },
    "missed_dose": {
        "patterns": ["miss a dose", "missed a vaccine", "what if i miss", "forgot vaccine",
                     "skip vaccine", "missed dose", "delayed vaccine", "late vaccine",
                     "overdue vaccine", "catch up vaccine", "missed vaccination"],
        "responses": [
            "⏰ **Missed a Vaccine? Don't Panic!**\n\nMost vaccines can be given **late** — you generally **don't need to restart** the series from the beginning.\n\n✅ **What to do:**\n1. Schedule the missed dose as soon as possible\n2. Continue the rest of the schedule from where you left off\n3. Tell your healthcare provider about the delay\n\n⚠️ **Why timing matters:** Some vaccines work best when given at specific ages. Delays may reduce effectiveness.\n\n📱 Use SmartVax's dashboard to see your overdue vaccines and get back on track!"
        ],
        "suggestions": ["View my schedule", "Set a reminder", "AI recommendations"]
    },

    # ── SPECIFIC VACCINES ───────────────────────────────────────────────────
    "bcg_vaccine": {
        "patterns": ["bcg", "bcg vaccine", "tuberculosis vaccine", "tb vaccine",
                     "what is bcg", "bcg vaccination"],
        "responses": [
            "🦠 **BCG Vaccine (Bacillus Calmette-Guérin)**\n\n**Protects against:** Tuberculosis (TB)\n**Given at:** Birth\n**Type:** Live-attenuated\n\n**Disease: Tuberculosis**\n• **Cause:** *Mycobacterium tuberculosis* — spread through air droplets\n• **Symptoms:** Persistent cough, night sweats, weight loss, fever, chest pain\n• **Risk:** Can affect lungs, brain (meningitis), kidneys, spine\n• **Global impact:** TB kills ~1.5 million people per year\n\n✅ **BCG effectiveness:** 70–80% effective against severe TB in children\n💉 **How given:** Single intradermal injection in the left upper arm at birth"
        ],
        "suggestions": ["DPT vaccine", "What is tuberculosis?", "Vaccine schedule"]
    },
    "dpt_vaccine": {
        "patterns": ["dpt", "dtap", "dpt vaccine", "diphtheria vaccine", "pertussis vaccine",
                     "tetanus vaccine", "whooping cough vaccine", "what is dpt", "tdap"],
        "responses": [
            "💉 **DPT/DTaP Vaccine**\n\n**Protects against:** Diphtheria, Pertussis (Whooping Cough), Tetanus\n**Schedule:** 2, 3, 4 months + booster at 18 months + pre-school booster\n\n🔴 **Diphtheria:** Creates a thick membrane in throat → breathing obstruction, heart damage. Fatal in 5–10%.\n\n🔴 **Pertussis:** Severe coughing fits with 'whoop' sound. Dangerous for infants under 6 months.\n\n🔴 **Tetanus (Lockjaw):** Painful muscle spasms, locked jaw — fatal in 10–20% of cases.\n\n✅ The DPT vaccine is one of the most effective vaccines — 95%+ protection!"
        ],
        "suggestions": ["What is whooping cough?", "Tetanus disease", "Vaccine side effects"]
    },
    "polio_vaccine": {
        "patterns": ["polio", "polio vaccine", "opv", "ipv", "oral polio",
                     "poliomyelitis", "what is polio vaccine"],
        "responses": [
            "💧 **Polio Vaccines (OPV & IPV)**\n\n**OPV** — Oral drops | **IPV** — Injection\n**Schedule:** Birth, 2, 3, 4 months + boosters\n\n🦠 **Disease: Poliomyelitis**\n• **Cause:** Poliovirus — spread through contaminated food/water\n• **Paralytic Polio:** Attacks spinal cord → permanent muscle paralysis\n• **No cure** — only prevention through vaccination\n\n🌍 Wild poliovirus has been eradicated from all but 2 countries thanks to global vaccination!\n\n✅ IPV is 99% effective after 3 doses"
        ],
        "suggestions": ["What is polio disease?", "OPV vs IPV", "Vaccine schedule"]
    },
    "hepatitis_b_vaccine": {
        "patterns": ["hepatitis b", "hep b", "hepatitis b vaccine", "what is hepatitis b",
                     "liver infection vaccine", "hbv vaccine"],
        "responses": [
            "🔴 **Hepatitis B Vaccine**\n\n**Schedule:** Birth + 2 months + 4 months + 6 months\n**Type:** Recombinant subunit\n\n🦠 **Disease: Hepatitis B**\n• **Cause:** HBV — spread through blood, sexual contact, mother to baby at birth\n• **Chronic infection:** 90% of infected infants develop chronic HBV\n• **Long-term dangers:** Liver cirrhosis, liver failure, liver cancer\n• **Global burden:** ~296 million with chronic Hep B; ~820,000 die annually\n\n✅ 95%+ effective at preventing infection\n🌟 It's the **first cancer-prevention vaccine** — prevents liver cancer!"
        ],
        "suggestions": ["Hepatitis A vaccine", "What is hepatitis?", "Liver disease"]
    },
    "hepatitis_a_vaccine": {
        "patterns": ["hepatitis a", "hep a", "hepatitis a vaccine", "what is hepatitis a"],
        "responses": [
            "🟡 **Hepatitis A Vaccine**\n\n**Schedule:** 12 months + 18 months (2 doses)\n**Type:** Inactivated virus\n\n🦠 **Disease: Hepatitis A**\n• **Cause:** HAV — spread through contaminated food/water or close contact\n• **Symptoms:** Sudden fever, jaundice, dark urine, nausea, abdominal pain\n• **Key difference from Hep B:** Hepatitis A does NOT become chronic — most recover fully\n• **Duration:** Illness lasts 2–6 weeks\n\n✅ Two doses provide lifelong protection — 95%+ effectiveness"
        ],
        "suggestions": ["Hepatitis B vaccine", "What is hepatitis?", "Typhoid vaccine"]
    },
    "mmr_vaccine": {
        "patterns": ["mmr", "mmr vaccine", "measles vaccine", "mumps vaccine",
                     "rubella vaccine", "what is mmr", "german measles"],
        "responses": [
            "🔴 **MMR Vaccine (Measles, Mumps, Rubella)**\n\n**Schedule:** 9 months (Dose 1) + 15 months (Dose 2) + 5 years (Dose 3)\n**Type:** Live-attenuated (3-in-1 combo)\n\n🔴 **Measles:** R0 = 12–18 (most contagious). Complications: pneumonia, encephalitis, death.\n\n🔵 **Mumps:** Swollen salivary glands. Complications: meningitis, deafness.\n\n🟣 **Rubella:** Devastating during pregnancy — Congenital Rubella Syndrome causes heart defects, deafness, blindness.\n\n✅ MMR is 97% effective against measles, 97% against rubella"
        ],
        "suggestions": ["What is measles?", "Vaccine safety", "Herd immunity"]
    },
    "varicella_vaccine": {
        "patterns": ["varicella", "chickenpox vaccine", "chickenpox", "varicella vaccine",
                     "what is varicella", "chicken pox"],
        "responses": [
            "🐔 **Varicella (Chickenpox) Vaccine**\n\n**Schedule:** 12 months + 18 months (2 doses)\n**Type:** Live-attenuated\n\n🦠 **Disease: Chickenpox**\n• **Cause:** Varicella-Zoster Virus (VZV) — spread through air and direct contact\n• **Symptoms:** Itchy fluid-filled blisters, fever, fatigue\n• **Reactivation:** Stays dormant in nerves → can reactivate as **Shingles** decades later\n\n✅ 2 doses are 98% effective at preventing chickenpox"
        ],
        "suggestions": ["Shingles vaccine", "What is shingles?", "Side effects"]
    },
    "hpv_vaccine": {
        "patterns": ["hpv", "hpv vaccine", "human papillomavirus", "cervical cancer vaccine",
                     "gardasil", "what is hpv"],
        "responses": [
            "🎗️ **HPV Vaccine (Human Papillomavirus)**\n\n**Schedule:** 10–12 years (2 doses, 6 months apart)\n**Type:** Recombinant subunit\n\n🦠 **HPV causes:**\n• Cervical cancer (HPV 16 & 18 cause 70% of cases)\n• Anal, throat, penile, vaginal cancers\n• Genital warts (HPV 6 & 11)\n\n✅ **Gardasil 9** protects against 9 HPV strains — up to 99% effective against cervical cancer\n🌟 One of only 2 **cancer-preventing vaccines**!\n👦👧 Recommended for **both boys and girls**"
        ],
        "suggestions": ["Cervical cancer prevention", "HPV schedule", "Hepatitis B vaccine"]
    },
    "flu_vaccine": {
        "patterns": ["flu vaccine", "influenza vaccine", "flu shot", "influenza", "flu prevention",
                     "annual flu", "what is flu vaccine", "seasonal flu"],
        "responses": [
            "🤧 **Influenza (Flu) Vaccine**\n\n**Schedule:** Annual — especially for 6+ months, elderly, pregnant women, healthcare workers\n\n🦠 **Disease: Influenza**\n• **Cause:** Influenza A or B viruses — respiratory droplets\n• **Symptoms:** Sudden high fever (38–40°C), severe muscle aches, fatigue, dry cough\n• **Key difference from cold:** Flu comes on suddenly and is much more severe\n• **Global burden:** 250,000–500,000 deaths/year\n\n⚠️ **Why annual?** Influenza viruses mutate rapidly — vaccine updated every year\n\n✅ Flu vaccine reduces serious illness by 40–60%"
        ],
        "suggestions": ["Side effects", "Adult vaccines", "Travel vaccines"]
    },
    "covid_vaccine": {
        "patterns": ["covid", "covid-19", "corona vaccine", "covid vaccine", "covid shot",
                     "covid booster", "coronavirus vaccine", "pfizer", "moderna", "covaxin",
                     "covishield", "what is covid vaccine"],
        "responses": [
            "🦠 **COVID-19 Vaccines**\n\n**Types:** mRNA (Pfizer/Moderna), Viral vector (AstraZeneca), Inactivated (Covaxin)\n**Schedule:** Primary series (2 doses) + boosters as recommended\n\n🦠 **Disease: COVID-19**\n• **Cause:** SARS-CoV-2 — respiratory droplets and aerosols\n• **Symptoms:** Fever, dry cough, shortness of breath, loss of taste/smell\n• **Severe cases:** Pneumonia, ARDS, organ failure\n• **Long COVID:** Persistent symptoms for weeks/months\n\n✅ **mRNA vaccines:** 90–95% effective at preventing severe disease\n\n💡 mRNA vaccines **cannot** alter your DNA. mRNA breaks down within days."
        ],
        "suggestions": ["mRNA vaccine types", "Vaccine safety", "COVID booster"]
    },
    "rotavirus_vaccine": {
        "patterns": ["rotavirus", "rotavirus vaccine", "diarrhea vaccine", "gastroenteritis vaccine",
                     "what is rotavirus"],
        "responses": [
            "💧 **Rotavirus Vaccine**\n\n**Schedule:** 2 months + 3 months (oral drops)\n**Type:** Live-attenuated (given orally)\n\n🦠 **Disease: Rotavirus Gastroenteritis**\n• **Cause:** Rotavirus — most common cause of severe diarrhea in infants worldwide\n• **Spread:** Fecal-oral route (contaminated hands, surfaces, food, water)\n• **Symptoms:** Severe watery diarrhea, vomiting, fever\n• **Danger:** Severe dehydration — leading cause of death in children under 5\n• **Global burden:** ~200,000 child deaths/year\n\n✅ Rotavirus vaccine reduces severe disease by 85–98%"
        ],
        "suggestions": ["What is diarrhea disease?", "Typhoid vaccine", "Vaccine schedule"]
    },
    "pcv_vaccine": {
        "patterns": ["pcv", "pneumococcal vaccine", "pneumonia vaccine", "pcv vaccine",
                     "what is pcv", "streptococcus pneumoniae"],
        "responses": [
            "🫁 **PCV — Pneumococcal Conjugate Vaccine**\n\n**Schedule:** 2 months + 4 months + 12 months\n**Type:** Conjugate\n\n🦠 **Disease: Pneumococcal Disease**\n• **Cause:** *Streptococcus pneumoniae* — respiratory droplets\n• **Diseases caused:** Pneumonia, Meningitis, Septicemia, Ear infections\n• **At risk:** Children under 2, elderly 65+, immunocompromised\n• **Global burden:** ~1.6 million deaths/year\n\n✅ PCV13/PCV15 protects against the 13–15 most dangerous strains — 75–90% effective"
        ],
        "suggestions": ["Meningitis vaccine", "Pneumonia disease", "Vaccine schedule"]
    },
    "typhoid_vaccine": {
        "patterns": ["typhoid", "typhoid vaccine", "typhoid fever", "what is typhoid",
                     "vi polysaccharide vaccine"],
        "responses": [
            "🌡️ **Typhoid Conjugate Vaccine (TCV)**\n\n**Schedule:** 2 years old (single dose)\n\n🦠 **Disease: Typhoid Fever**\n• **Cause:** *Salmonella typhi* — contaminated food and water\n• **Symptoms:** Sustained high fever (40°C), severe headache, abdominal pain, weakness\n• **Danger:** Intestinal perforation, internal bleeding, organ failure\n• **Global burden:** 11–20 million cases/year; ~161,000 deaths\n\n✅ Conjugate typhoid vaccine is 80–90% effective"
        ],
        "suggestions": ["Hepatitis A vaccine", "Travel vaccines", "Vaccine schedule"]
    },
    "meningococcal_vaccine": {
        "patterns": ["meningococcal", "meningitis vaccine", "meningococcal vaccine",
                     "what is meningitis", "bacterial meningitis"],
        "responses": [
            "🧠 **Meningococcal Vaccine**\n\n**Schedule:** 12–16 years + booster at 16–18 years\n**Type:** Conjugate\n\n🦠 **Disease: Bacterial Meningitis**\n• **Cause:** *Neisseria meningitidis* — respiratory droplets\n• **Symptoms:** Sudden high fever, intense headache, stiff neck, non-fading rash\n• ⚠️ **The non-fading rash + fever is a medical emergency!**\n• **Can cause death within 24 hours** even with treatment\n• **Fatality rate:** 10–15%\n\n✅ Meningococcal vaccines are 85–90% effective"
        ],
        "suggestions": ["PCV vaccine", "What is meningitis?", "Emergency symptoms"]
    },

    # ── SPECIFIC DISEASES ─────────────────────────────────────────────────
    "tuberculosis_disease": {
        "patterns": ["what is tuberculosis", "what is tb", "tuberculosis symptoms",
                     "tb disease", "how is tb spread", "tuberculosis causes", "tb treatment"],
        "responses": [
            "🦠 **Tuberculosis (TB)**\n\n**Cause:** *Mycobacterium tuberculosis*\n**Spread:** Airborne — coughing, sneezing, speaking. NOT by touching.\n\n**Symptoms (Pulmonary TB):**\n• Persistent cough lasting 3+ weeks\n• Coughing blood, night sweats, weight loss, fatigue\n\n**Latent TB:** 25% of world population are infected but have no symptoms — can activate later.\n\n**Treatment:** 6-month course of antibiotics (RIPE regimen)\n**Prevention:** 💉 BCG vaccine"
        ],
        "suggestions": ["BCG vaccine", "Lung diseases", "Vaccine schedule"]
    },
    "measles_disease": {
        "patterns": ["what is measles", "measles symptoms", "measles disease",
                     "how does measles spread", "measles causes", "rubeola"],
        "responses": [
            "🔴 **Measles (Rubeola)**\n\n**Cause:** Measles virus — 90% of unvaccinated people exposed will get infected!\n**Spread:** Air droplets; virus remains infectious in air for up to 2 hours.\n\n**Symptoms:**\n1. High fever (up to 40.6°C)\n2. The 3 C's: Cough, Coryza (runny nose), Conjunctivitis\n3. Koplik's spots (tiny white spots inside mouth)\n4. Full-body red blotchy rash\n\n**Complications:** Pneumonia (1 in 20), Encephalitis (1 in 1,000), Permanent deafness, Death\n\n**Prevention:** 💉 MMR vaccine (2 doses give 97% protection)"
        ],
        "suggestions": ["MMR vaccine", "Vaccine safety", "Herd immunity"]
    },
    "tetanus_disease": {
        "patterns": ["what is tetanus", "tetanus disease", "lockjaw", "tetanus symptoms",
                     "how tetanus spreads", "tetanus causes", "tetanus treatment"],
        "responses": [
            "⚠️ **Tetanus (Lockjaw)**\n\n**Cause:** Toxin from *Clostridium tetani* — found in soil, dust, animal feces\n**Entry:** Through cuts, wounds, punctures, burns, animal bites. NOT spread person-to-person.\n\n**Symptoms:**\n• Lockjaw — inability to open mouth\n• Muscle stiffness and spasms (neck, abdomen, back)\n• Difficulty swallowing, arched back\n• Severe spasms can fracture bones!\n\n**Fatality rate:** 10–20% even with treatment\n**Treatment:** Tetanus antitoxin + antibiotics + muscle relaxants\n\n**Prevention:** 💉 DPT vaccine + boosters every 10 years"
        ],
        "suggestions": ["DPT vaccine", "Wound care", "Adult boosters"]
    },
    "hepatitis_disease": {
        "patterns": ["what is hepatitis", "hepatitis disease", "types of hepatitis",
                     "hepatitis symptoms", "hepatitis causes", "liver disease"],
        "responses": [
            "🔴 **Hepatitis (Liver Inflammation)**\n\n**Types:**\n| Type | Cause | Spread | Vaccine? |\n|------|-------|--------|----------|\n| **Hep A** | HAV | Food/water | ✅ Yes |\n| **Hep B** | HBV | Blood, sex, birth | ✅ Yes |\n| **Hep C** | HCV | Blood, needles | ❌ No |\n| **Hep D** | HDV | Only with Hep B | ✅ Via Hep B |\n\n**Common symptoms:** Jaundice, dark urine, fatigue, abdominal pain, nausea\n\n**Serious outcomes (Hep B & C):** Chronic → cirrhosis → liver cancer\n\n💉 Get vaccinated for Hepatitis A and B!"
        ],
        "suggestions": ["Hepatitis A vaccine", "Hepatitis B vaccine", "Liver protection"]
    },
    "whooping_cough_disease": {
        "patterns": ["what is whooping cough", "pertussis", "pertussis disease",
                     "whooping cough symptoms", "pertussis symptoms", "pertussis causes"],
        "responses": [
            "😷 **Whooping Cough (Pertussis)**\n\n**Cause:** *Bordetella pertussis* — highly contagious airborne bacteria\n\n**Stages:**\n1. **Catarrhal (1–2 wks):** Mild cold symptoms\n2. **Paroxysmal (1–6 wks):** Severe coughing fits, the 'whoop' gasp, turning red/blue\n3. **Convalescent:** Gradual recovery, lingering cough\n\n**Most dangerous for:** Infants under 6 months — can stop breathing\n\n**Complications:** Pneumonia, rib fractures, brain damage\n\n**Prevention:** 💉 DPT vaccine + Tdap booster for pregnant women"
        ],
        "suggestions": ["DPT vaccine", "Infant vaccination", "Pregnancy vaccines"]
    },

    # ── SCHEDULE & SPECIFIC QUERIES ────────────────────────────────────────
    "child_vaccines": {
        "patterns": [
            "vaccines for children", "vaccines recommended for children",
            "what vaccines are recommended for children", "children vaccination",
            "recommended vaccines for children", "what vaccines do children need",
            "kids vaccines", "vaccines for kids", "vaccines for infants",
            "what vaccines are needed for children", "child immunization",
            "pediatric vaccines", "vaccines for toddlers", "newborn vaccines",
            "vaccines for babies", "recommended childhood vaccines"
        ],
        "responses": [
            "👶 **Vaccines Recommended for Children:**\n\n🍼 **At Birth:** BCG, Hepatitis B-1, OPV-0\n📅 **2 Months:** DPT-1, Hep B-2, OPV-1, Rotavirus-1, PCV-1\n📅 **3 Months:** DPT-2, OPV-2, Rotavirus-2\n📅 **4 Months:** DPT-3, OPV-3, Hep B-3, PCV-2\n📅 **6 Months:** Influenza, Hep B-4\n📅 **9 Months:** MMR-1, Vitamin A\n📅 **12 Months:** PCV booster, Varicella-1, Hep A-1\n📅 **15 Months:** MMR-2\n📅 **18 Months:** DPT booster, OPV booster, Hep A-2, Varicella-2\n📅 **2 Years:** Typhoid\n📅 **4–6 Years:** DTaP booster, MMR-3\n📅 **10–12 Years:** HPV vaccine (2 doses)\n\n💡 These follow WHO & national immunization program guidelines.\n📱 Check your SmartVax **Schedule** tab for your personalized vaccination timeline!"
        ],
        "suggestions": ["BCG vaccine", "MMR vaccine", "DPT vaccine"]
    },
    "vaccine_schedule": {
        "patterns": ["vaccine schedule", "vaccination schedule", "when to vaccinate",
                     "immunization schedule", "childhood vaccines", "baby vaccines",
                     "infant vaccination", "schedule of vaccines", "complete schedule",
                     "full vaccination schedule", "immunization chart"],
        "responses": [
            "📅 **Vaccination Schedule (Birth to Adult):**\n\n**At Birth:** BCG, Hepatitis B-1, OPV-0\n**2 Months:** DPT-1, Hep B-2, OPV-1, Rotavirus-1, PCV-1\n**3 Months:** DPT-2, OPV-2, Rotavirus-2\n**4 Months:** DPT-3, OPV-3, Hep B-3, PCV-2\n**6 Months:** Influenza, Hep B-4\n**9 Months:** MMR-1, Vitamin A\n**12 Months:** PCV booster, Varicella-1, Hep A-1\n**15 Months:** MMR-2\n**18 Months:** DPT booster, OPV booster, Hep A-2, Varicella-2\n**2 Years:** Typhoid\n**4–6 Years:** DTaP booster, IPV booster, MMR-3\n**10–12 Years:** HPV (2 doses)\n**Adults:** Influenza (annual), Td every 10 years, COVID-19\n\n📱 **Your personalized schedule** is in SmartVax — check your Schedule tab!"
        ],
        "suggestions": ["Next vaccine", "Adult vaccines", "COVID-19 vaccine"]
    },
    "next_vaccine": {
        "patterns": ["next vaccine", "upcoming vaccine", "when is my next vaccine",
                     "what vaccine is next", "my next shot", "when should i get vaccinated"],
        "responses": [
            "📅 Your upcoming vaccines are shown in real-time on your **SmartVax Dashboard** and **Schedule** page!\n\nThe system calculates your next due vaccines based on your age and vaccination history.\n🔴 Red = Overdue | 🟡 Yellow = Upcoming soon | 🔵 Blue = Future\n\nGo to the **Schedule** tab to see your full personalized vaccine timeline! 💉"
        ],
        "suggestions": ["Open schedule", "Set a reminder", "AI recommendations"]
    },
    "adult_vaccines": {
        "patterns": ["adult vaccines", "vaccines for adults", "which vaccines do adults need",
                     "adult vaccination", "what vaccines should adults get"],
        "responses": [
            "👨‍💼 **Vaccines for Adults:**\n\n• **Influenza** — Annually, especially 65+, pregnant women, healthcare workers\n• **Td/Tdap booster** — Every 10 years\n• **COVID-19** — Primary series + boosters\n• **Hepatitis A & B** — If not previously vaccinated\n• **HPV** — Up to age 26 (or 27–45 if recommended)\n• **Pneumococcal (PCV)** — Age 65+ or younger with diabetes/heart disease\n• **Shingles (Zoster)** — Age 50+ (2-dose Shingrix)\n• **Meningococcal** — College students, travelers to high-risk areas\n\nCheck your SmartVax AI Recommendations for what YOU need! 📊"
        ],
        "suggestions": ["Shingles vaccine", "Influenza vaccine", "Td booster"]
    },
    "pregnancy_vaccines": {
        "patterns": ["pregnancy vaccine", "vaccine during pregnancy", "pregnant vaccination",
                     "vaccines for pregnant", "prenatal vaccine"],
        "responses": [
            "🤰 **Vaccines During Pregnancy:**\n\n✅ **Safe & Recommended:**\n• **Tdap** — At 27–36 weeks → protects newborn from whooping cough\n• **Influenza** — Every pregnancy season\n• **COVID-19** — Recommended; reduces severe illness risk\n\n⚠️ **Avoid (live vaccines):**\n• MMR, Varicella, OPV — Give before pregnancy or after delivery\n\n💡 Vaccines in pregnancy transfer antibodies through the placenta — protecting your baby immediately after birth when they're too young for vaccines!"
        ],
        "suggestions": ["DPT vaccine", "Infant schedule", "Vaccine safety"]
    },
    "travel_vaccines": {
        "patterns": ["travel vaccine", "vaccines for travel", "travel vaccination",
                     "which vaccines before travel", "international travel vaccine"],
        "responses": [
            "✈️ **Travel Vaccines:**\n\nBefore international travel, check vaccination status for:\n\n• **Yellow Fever** — Required for many African and South American countries\n• **Typhoid** — South Asia, Africa, Latin America\n• **Hepatitis A** — Any destination with poor sanitation\n• **Meningococcal** — Saudi Arabia (Hajj), sub-Saharan Africa\n• **Japanese Encephalitis** — Southeast Asia, rural areas\n• **Rabies** — If working with animals in endemic areas\n\n⏰ **Plan ahead** — some travel vaccines need 4–8 weeks before departure!\nConsult a travel health clinic for personalized advice."
        ],
        "suggestions": ["Typhoid vaccine", "Hepatitis A vaccine", "Yellow fever"]
    },
    "shingles_vaccine": {
        "patterns": ["shingles", "shingles vaccine", "herpes zoster", "zoster vaccine",
                     "shingrix", "what is shingles"],
        "responses": [
            "⚡ **Shingles (Herpes Zoster)**\n\n**What it is:** Reactivation of the chickenpox virus (VZV) that stayed dormant in nerve tissue\n\n**Symptoms:**\n• Burning, shooting pain along a nerve path\n• Blistering rash on one side of body\n• **Post-herpetic neuralgia (PHN):** Severe nerve pain lasting months after rash heals — affects 20% of patients\n\n**Risk after 50:** 50% of people who live to age 85 will get shingles\n\n**Vaccine:** 💉 **Shingrix** (2 doses) — recommended at age 50+\n• 97% effective in 50–69 year-olds\n• 91% effective in 70+ year-olds"
        ],
        "suggestions": ["Varicella vaccine", "Adult vaccines", "Side effects"]
    },

    # ── SMARTVAX FEATURES ──────────────────────────────────────────────────
    "risk_prediction": {
        "patterns": ["high risk", "low risk", "risk prediction", "am i at risk",
                     "risk assessment", "missed dose risk", "vaccination risk"],
        "responses": [
            "⚠️ **SmartVax Risk Prediction:**\n\nOur AI model (Random Forest) assesses your risk of **missing upcoming vaccine doses** based on:\n• Your vaccination completion rate\n• Number of pending/overdue vaccines\n• Days since your last vaccine\n• Your age and profile completeness\n\n🔴 **High Risk** = Schedule appointments soon\n🟢 **Low Risk** = You're on track!\n\nCheck your **Dashboard** for your current risk score and confidence level. 📊"
        ],
        "suggestions": ["View dashboard", "AI recommendations", "Set reminders"]
    },
    "recommendation_page": {
        "patterns": ["ai recommendation", "vaccine recommendation", "what vaccine do i need",
                     "personalized recommendation", "which vaccine should i get"],
        "responses": [
            "🤖 **SmartVax AI Recommendations:**\n\nOur AI engine analyzes your **age, vaccination history, and health profile** to recommend vaccines specifically suited to you.\n\nVisit the **AI Recommendations** tab to see:\n• 🔴 High Priority — Vaccines due now (overdue)\n• 🟡 Medium Priority — Upcoming (next 3 months)\n• 🔵 Low Priority — Future vaccines\n• Your risk level prediction with confidence score\n\nAll recommendations are based on WHO and national immunization programs! 📋"
        ],
        "suggestions": ["Open recommendations", "Risk prediction", "Vaccine schedule"]
    },
    "pdf_report": {
        "patterns": ["pdf report", "download report", "vaccination certificate",
                     "vaccine record", "vaccination report", "vaccination history report"],
        "responses": [
            "📄 **Download Your Vaccination Report:**\n\nYou can download a personalized PDF vaccination report from SmartVax at any time!\n\nThe report includes:\n• Your personal information\n• Summary (total completed vs pending)\n• All completed vaccinations (with dates)\n• Pending vaccinations\n\n👆 Click **Report** in the top navbar, or use the **PDF Report** button on your Dashboard. Keep it for school, work, or medical visits! 💼"
        ],
        "suggestions": ["Download now", "AI recommendations", "View history"]
    },
    "reminder": {
        "patterns": ["reminder", "notification", "remind me", "vaccine alert",
                     "upcoming reminder", "vaccine notification", "email reminder"],
        "responses": [
            "🔔 **SmartVax Reminders:**\n\nSet personalized reminders for your upcoming vaccines:\n• Choose how many days before to be notified (7, 14, 30 days)\n• Set preferred notification time\n• Enter your appointment date\n• Toggle reminders ON/OFF anytime\n\n📧 **Email reminders** are automatically sent when a vaccine is due or overdue — if email is configured.\n\nGo to the **Reminders** tab to set up your alerts! 📅"
        ],
        "suggestions": ["Open reminders", "Overdue vaccines", "View schedule"]
    },
    "immune_system": {
        "patterns": ["immune system", "immunity", "how immune system works",
                     "antibodies", "what are antibodies", "innate immunity",
                     "adaptive immunity", "how body fights disease"],
        "responses": [
            "🛡️ **How the Immune System Works:**\n\n**Two main branches:**\n\n1️⃣ **Innate Immunity (First line of defense)**\n• Skin, mucus, stomach acid\n• Non-specific — attacks anything foreign\n• Responds within minutes to hours\n\n2️⃣ **Adaptive Immunity (Specific defense)**\n• **B-cells** → produce antibodies\n• **T-cells** → kill infected cells, coordinate immune response\n• Creates **immunological memory** — remembers pathogens for years\n• Takes 1–2 weeks to build; faster on re-exposure\n\n💉 Vaccines safely trigger adaptive immunity without causing disease!"
        ],
        "suggestions": ["How vaccines work", "Herd immunity", "Antibodies explained"]
    },
    "vitamin_a": {
        "patterns": ["vitamin a", "vitamin a supplement", "what is vitamin a supplementation"],
        "responses": [
            "🟠 **Vitamin A Supplementation**\n\n**Schedule:** Given at 9 months, 18 months, then every 6 months until age 5\n\n**Why it matters:**\n• Essential for immune function and vision\n• Deficiency increases severity of infections like measles and diarrhea\n• Causes **night blindness** → eventually full blindness (xerophthalmia)\n\n**Impact:**\n• Reduces child mortality by 12–24%\n• Reduces measles-related deaths by 50%\n• Prevents blindness in ~500,000 children/year\n\nNOT a vaccine but co-administered with vaccines at 9 months in many programs. 💊"
        ],
        "suggestions": ["MMR vaccine", "Measles disease", "Child immunization"]
    },
}

# ── Fallback responses ────────────────────────────────────────────────────
DEFAULT_RESPONSES = [
    "🤔 I'm not sure about that. Did you mean one of these?\n• **Vaccination schedule** — when to get vaccinated\n• **Specific vaccines** — BCG, MMR, DPT, COVID-19, HPV\n• **Side effects** — what to expect after vaccination\n• **Missed doses** — what to do if you've missed a vaccine\n\nTry rephrasing your question!",
    "That's outside my current knowledge area. 😊 I can answer questions about:\n• **Vaccine types** — live, inactivated, mRNA, subunit\n• **Diseases** — measles, polio, TB, hepatitis, COVID-19\n• **Schedules** — when to get vaccinated at each age\n• **Safety & side effects**\n\nTry asking something like '*What is the MMR vaccine?*' or '*what are side effects?*'",
    "🏥 For specific medical advice about your health condition, please consult your healthcare provider.\n\nI can help with general vaccine and disease information!\n\n💡 **Try asking:**\n• 'What is vaccination?'\n• 'Tell me about the BCG vaccine'\n• 'How does herd immunity work?'"
]

# ── Spell-correction shortcuts ─────────────────────────────────────────────
COMMON_CORRECTIONS = {
    'vacine': 'vaccine', 'vaccene': 'vaccine', 'vacination': 'vaccination',
    'immunisation': 'immunization', 'hep': 'hepatitis', 'mealses': 'measles',
    'pollio': 'polio', 'tetnus': 'tetanus', 'covis': 'covid',
    'recomended': 'recommended', 'reccomended': 'recommended',
    'childern': 'children', 'childs': 'children', 'babys': 'babies',
    'imunization': 'immunization', 'shedule': 'schedule',
}


class VaccineChatbot:
    """Enhanced NLP vaccine chatbot with intent classification and confidence scoring."""

    def __init__(self):
        self.intents = INTENTS
        self.conversation_history = []

    # ── Text preprocessing ────────────────────────────────────────────────
    def _preprocess(self, text: str) -> str:
        text = text.lower().strip()
        # Apply common corrections
        for wrong, right in COMMON_CORRECTIONS.items():
            text = text.replace(wrong, right)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _tokenize(self, text: str) -> list:
        return text.split()

    # ── Scoring ───────────────────────────────────────────────────────────
    def _calculate_score(self, user_tokens: list, processed: str, pattern: str) -> float:
        pattern_clean = re.sub(r'[^\w\s]', ' ', pattern.lower()).strip()
        score = 0.0
        # Exact phrase match — highest priority
        if pattern_clean in processed:
            score += 2.0
        # Word overlap score
        pattern_words = pattern_clean.split()
        matches = sum(1 for w in pattern_words if w in user_tokens)
        if pattern_words:
            score += matches / len(pattern_words)
        return score

    # ── Intent detection ──────────────────────────────────────────────────
    def _detect_intent(self, user_input: str) -> tuple:
        """Detect intent; returns (intent_name, raw_score, normalized_confidence)."""
        processed = self._preprocess(user_input)
        tokens = self._tokenize(processed)
        best_intent = None
        best_score = 0.0

        for intent_name, intent_data in self.intents.items():
            for pattern in intent_data['patterns']:
                score = self._calculate_score(tokens, processed, pattern)
                if score > best_score:
                    best_score = score
                    best_intent = intent_name

        # Threshold for accepting a match
        if best_score >= 0.4:
            # Normalize to 0–1 confidence (cap at max score of 3.0)
            confidence = min(best_score / 3.0, 1.0)
            return best_intent, confidence

        return None, 0.0

    # ── Suggestion generator ───────────────────────────────────────────────
    def _get_contextual_suggestions(self, intent: str) -> list:
        """Return intent-specific suggestions when available."""
        if intent and intent in self.intents:
            intent_suggestions = self.intents[intent].get('suggestions', [])
            if intent_suggestions:
                return intent_suggestions[:3]
        return self.get_suggestions()[:4]

    # ── Main response ─────────────────────────────────────────────────────
    def get_response(self, user_input: str) -> dict:
        """Process user input and return a response dict."""
        if not user_input or not user_input.strip():
            return {
                'response': "Please type a question and I'll help you! 😊",
                'intent': 'empty',
                'intent_display': 'No input',
                'confidence': 0.0,
                'confidence_label': 'N/A',
                'suggestions': self.get_suggestions()[:4],
                'timestamp': datetime.now().strftime('%H:%M')
            }

        intent, confidence = self._detect_intent(user_input)

        if intent and intent in self.intents:
            response = random.choice(self.intents[intent]['responses'])
            intent_display = intent.replace('_', ' ').title()
        else:
            response = random.choice(DEFAULT_RESPONSES)
            intent = 'unknown'
            intent_display = 'General Help'
            confidence = 0.0

        # Human-readable confidence label
        if confidence >= 0.75:
            confidence_label = 'High'
        elif confidence >= 0.45:
            confidence_label = 'Medium'
        elif confidence > 0:
            confidence_label = 'Low'
        else:
            confidence_label = 'Unmatched'

        self.conversation_history.append({
            'user': user_input,
            'bot': response,
            'intent': intent,
            'timestamp': datetime.now().strftime('%H:%M')
        })

        return {
            'response': response,
            'intent': intent,
            'intent_display': intent_display,
            'confidence': round(confidence * 100, 1),
            'confidence_label': confidence_label,
            'suggestions': self._get_contextual_suggestions(intent),
            'timestamp': datetime.now().strftime('%H:%M')
        }

    def get_suggestions(self) -> list:
        """Return suggested starter questions."""
        return [
            "What is vaccination?",
            "How do vaccines work?",
            "What is the MMR vaccine?",
            "What diseases does BCG prevent?",
            "What is polio and how does it spread?",
            "What are the side effects of vaccines?",
            "What is herd immunity?",
            "What vaccines do adults need?",
            "Tell me about the COVID-19 vaccine",
            "What is measles and how is it caused?",
            "When is my next vaccine due?",
            "What happens if I miss a vaccine dose?",
        ]


# ── Singleton instance ─────────────────────────────────────────────────────
chatbot = VaccineChatbot()
