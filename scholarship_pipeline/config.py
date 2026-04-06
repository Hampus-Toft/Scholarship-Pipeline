import pytesseract

MODE = "regions"
TARGET_SIZE = (2480, 3508)  # A4 at ~300 DPI
TESSERACT_CMD = "/opt/local/bin/tesseract"
POPLER_PATH = "/opt/local/bin"
PADDING = 0.00
INPUT_FOLDER = "input_images"
OUTPUT_FILE = "output.xlsx"

FIELDS_PAGE_1 = {
    "name": (0.15441, 0.29852, 0.34033, 0.0171),
    "personal_number_1": (0.2113, 0.3210, 0.0738, 0.0125),
    "personal_number_2": (0.2903, 0.3210, 0.0476, 0.0128),
    "birth_place": (0.1198, 0.3526, 0.7137, 0.0151),
    "is_citizen": (0.2649, 0.3777, 0.0335, 0.0105),
    "is_not_citizen": (0.3286, 0.3749, 0.0472, 0.0162),
    "period_is_ht": (0.1395, 0.3960, 0.0266, 0.0134),
    "period_is_vt": (0.1710, 0.3945, 0.0258, 0.0143),
    "period_year": (0.1996, 0.3945, 0.0246, 0.0140),
    "scholarships": (0.1157, 0.4085, 0.7331, 0.0687),
    "highschool": (0.3460, 0.4749, 0.1984, 0.0154),
    "hs_day": (0.5649, 0.4763, 0.0194, 0.0137),
    "hs_month": (0.5867, 0.4766, 0.0198, 0.0140),
    "hs_year": (0.6202, 0.4752, 0.0387, 0.0157),
    "hs_alternatives": (0.4601, 0.5202, 0.1976, 0.0188),
    "hsa_day": (0.7319, 0.5259, 0.0210, 0.0111),
    "hsa_month": (0.7552, 0.5228, 0.0190, 0.0168),
    "hsa_year": (0.7778, 0.5228, 0.0484, 0.0171),
    "uu_joined_ht": (0.3641, 0.5553, 0.0250, 0.0174),
    "uu_joined_vt": (0.3984, 0.5596, 0.0230, 0.0111),
    "uu_joined_year": (0.4246, 0.5550, 0.1294, 0.0123),
    "gh_joined_ht": (0.4000, 0.5767, 0.0238, 0.0134),
    "gh_joined_vt": (0.4331, 0.5773, 0.0214, 0.0108),
    "gh_joined_year": (0.4560, 0.5730, 0.0984, 0.0123),
    "nation_membership_1": (0.5778, 0.5924, 0.1492, 0.0140),
    "nation_membership_2": (0.1234, 0.6058, 0.6335, 0.0468),
    "other_periods_1": (0.4270, 0.6474, 0.3286, 0.0154),
    "other_periods_2": (0.1222, 0.6613, 0.6375, 0.0214),
    "break_periods_1": (0.2883, 0.6807, 0.4613, 0.0134),
    "break_periods_2": (0.1246, 0.6990, 0.6258, 0.0148),
    "credits_total": (0.2516, 0.7443, 0.1161, 0.0148),
    "credits_high": (0.1875, 0.7645, 0.1185, 0.0174),
    "credits_capped": (0.1790, 0.7816, 0.1242, 0.0154),
    "credits_high_level": (0.2597, 0.8007, 0.1141, 0.0188),
    "external_credits_total": (0.2508, 0.8421, 0.1206, 0.0097),
    "external_credits_high": (0.1851, 0.8552, 0.1198, 0.0145),
    "external_credits_capped": (0.1835, 0.8751, 0.1190, 0.0194),
    "external_credits_high_level": (0.2589, 0.8920, 0.1109, 0.0151),
}

# Configure second-page regions here.
# These are copied from page 1 as a safe starter so page-aware routing works immediately.
# Replace with page-2-specific coordinates from region_selector_web.py for correct extraction.
FIELDS_PAGE_2 = {
    "field": (0.2359, 0.0761, 0.1081, 0.0171),
    "period_ht": (0.5415, 0.0812, 0.0282, 0.0222),
    "period_vt": (0.5770, 0.0815, 0.0218, 0.0194),
    "period_year": (0.6012, 0.0795, 0.0508, 0.0200),

    "scholarship_name_1": (0.1194, 0.1385, 0.2585, 0.0157),
    "scholarship_start_day_1": (0.4169, 0.1408, 0.0246, 0.0171),
    "scholarship_start_mon_1": (0.4480, 0.1414, 0.0177, 0.0160),
    "scholarship_start_yea_1": (0.4681, 0.1434, 0.0387, 0.0137),
    "scholarship_end_day_1": (0.5476, 0.1411, 0.0149, 0.0143),
    "scholarship_end_mon_1": (0.5665, 0.1414, 0.0161, 0.0145),
    "scholarship_end_yea_1": (0.5843, 0.1420, 0.0399, 0.0157),
    "scholarship_amount_1": (0.6383, 0.1411, 0.0512, 0.0128),

    # "scholarship_name_2": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),

    # "scholarship_name_3": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    # "name": (...),
    
    "family_relation": (0.1198, 0.2118, 0.6097, 0.0157),

    "extra_curricular": (0.1190, 0.2489, 0.5694, 0.0345),

    "csn_remain": (0.4871, 0.2876, 0.0532, 0.0137),

    "period_subject": (0.2815, 0.3099, 0.1831, 0.0162),
    "period_points": (0.4875, 0.3121, 0.0298, 0.0145),
    "period_level": (0.5794, 0.3119, 0.0702, 0.0145),

    "signing_date": (0.1254, 0.4151, 0.2270, 0.0177),
    "name": (0.1254, 0.4823, 0.2185, 0.0197),

    "bank": (0.1262, 0.5279, 0.2262, 0.0180),
    "account": (0.1234, 0.5661, 0.2355, 0.0177),

    "street": (0.5125, 0.4441, 0.2871, 0.0205),
    "postcode": (0.5117, 0.4809, 0.2847, 0.0202),

    "email": (0.5125, 0.5279, 0.3242, 0.0222),
    "phone": (0.5129, 0.5790, 0.3242, 0.0205),
}

FIELDS_BY_PAGE = {
    1: FIELDS_PAGE_1,
    2: FIELDS_PAGE_2,
}

# Backwards-compatible alias used by existing code paths/tests.
FIELDS = FIELDS_PAGE_1


def configure_binaries():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
