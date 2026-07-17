"""Governed document corpus (synthetic, fictional carrier 'Acme Mutual').

Every chunk mirrors the metadata schema from the system design:
doc identity + version + status, jurisdiction, doc_type, clause_type,
section path, and ACL roles. The chunks are pre-cut along section
boundaries (the design's section-aware chunking) — in a full pipeline
this is the output of the ingestion stage.

status: active | superseded   (superseded is excluded from default scope)
jurisdiction: state code or "US" (countrywide)
acl_roles: which agent roles may retrieve the chunk
"""

CHUNKS: list[dict] = [
    # ---------------- HO-3 Texas, 2024 edition (ACTIVE) ----------------
    dict(
        doc_id="ho3_tx_2024", title="Homeowners 3 — Special Form (Texas)",
        form="HO 00 03", edition="2024", status="active", jurisdiction="TX",
        doc_type="policy_form", policy_type="homeowners",
        section_path="SECTION I > Exclusions > 1. Water Damage",
        clause_type="exclusion", acl_roles=["agent_personal", "underwriter"],
        text=(
            "We do not insure for loss caused directly or indirectly by water damage, "
            "meaning: (a) flood, surface water, waves, tidal water, or overflow of a body "
            "of water; (b) water which backs up through sewers or drains; or (c) water "
            "below the surface of the ground which exerts pressure on or seeps through a "
            "building, sidewalk, driveway, foundation, or swimming pool. However, we do "
            "insure for direct loss by fire, explosion, or theft resulting from water "
            "damage. Sudden and accidental discharge of water from a plumbing, heating, "
            "or air conditioning system within the dwelling is covered under Coverage A."
        ),
    ),
    dict(
        doc_id="ho3_tx_2024", title="Homeowners 3 — Special Form (Texas)",
        form="HO 00 03", edition="2024", status="active", jurisdiction="TX",
        doc_type="policy_form", policy_type="homeowners",
        section_path="SECTION I > Exclusions > 2. Earth Movement",
        clause_type="exclusion", acl_roles=["agent_personal", "underwriter"],
        text=(
            "We do not insure for loss caused by earth movement, meaning earthquake, "
            "landslide, mudflow, subsidence, or sinkhole collapse. Direct loss by fire or "
            "explosion resulting from earth movement is covered."
        ),
    ),
    dict(
        doc_id="ho3_tx_2024", title="Homeowners 3 — Special Form (Texas)",
        form="HO 00 03", edition="2024", status="active", jurisdiction="TX",
        doc_type="policy_form", policy_type="homeowners",
        section_path="SECTION I > Exclusions > 3. Neglect, Intentional Loss, War, Nuclear Hazard",
        clause_type="exclusion", acl_roles=["agent_personal", "underwriter"],
        text=(
            "We do not insure for loss caused by: neglect of the insured to use all "
            "reasonable means to save and preserve property at and after the time of a "
            "loss; intentional loss, meaning any loss arising out of an act committed by "
            "or at the direction of an insured with the intent to cause a loss; war, "
            "including undeclared war and civil war; or nuclear hazard."
        ),
    ),
    dict(
        doc_id="ho3_tx_2024", title="Homeowners 3 — Special Form (Texas)",
        form="HO 00 03", edition="2024", status="active", jurisdiction="TX",
        doc_type="policy_form", policy_type="homeowners",
        section_path="SECTION II > Conditions > Cancellation",
        clause_type="condition", acl_roles=["agent_personal", "underwriter"],
        text=(
            "Cancellation. The insured may cancel this policy at any time by returning it "
            "to us or notifying us in writing of the date cancellation is to take effect. "
            "We may cancel this policy only for the reasons stated below by letting the "
            "insured know in writing of the date cancellation takes effect. When the "
            "insured has not paid the premium, we may cancel at any time by notifying "
            "the insured at least 10 days before the date cancellation takes effect. When "
            "this policy has been in effect for less than 60 days and is not a renewal, "
            "we may cancel for any reason with at least 10 days notice."
        ),
    ),
    dict(
        doc_id="ho3_tx_2024", title="Homeowners 3 — Special Form (Texas)",
        form="HO 00 03", edition="2024", status="active", jurisdiction="TX",
        doc_type="policy_form", policy_type="homeowners",
        section_path="DEFINITIONS > Surface Water",
        clause_type="definition", acl_roles=["agent_personal", "underwriter"],
        text=(
            "'Surface water' means water on the surface of the ground, of a casual or "
            "vagrant character, that follows no definite course; it does not include "
            "water in a swimming pool or water escaping from a plumbing system."
        ),
    ),

    # ------------- HO-3 Texas, 2019 edition (SUPERSEDED) ---------------
    dict(
        doc_id="ho3_tx_2019", title="Homeowners 3 — Special Form (Texas)",
        form="HO 00 03", edition="2019", status="superseded", jurisdiction="TX",
        doc_type="policy_form", policy_type="homeowners",
        section_path="SECTION I > Exclusions > 1. Water Damage",
        clause_type="exclusion", acl_roles=["agent_personal", "underwriter"],
        text=(
            "2019 EDITION (superseded). We do not insure for loss caused by water damage, "
            "meaning flood, surface water, or overflow of a body of water. Sewer backup "
            "was not addressed in this edition and trampolines were not referenced."
        ),
    ),

    # ------ TX amendatory endorsement (ACTIVE, amends HO-3 TX) ---------
    dict(
        doc_id="ho_am_tx_2024", title="Texas Amendatory Endorsement",
        form="HO 01 42", edition="2024", status="active", jurisdiction="TX",
        doc_type="endorsement", policy_type="homeowners",
        amends="ho3_tx_2024",
        section_path="Paragraph B > Cancellation Notice",
        clause_type="endorsement_change", acl_roles=["agent_personal", "underwriter"],
        text=(
            "Texas Amendatory Endorsement HO 01 42. Paragraph 'Cancellation' of SECTION II "
            "Conditions is amended as follows: when this policy has been in effect for 60 "
            "days or more, we may cancel only for nonpayment of premium, fraud, or a "
            "material change in the risk, and we must provide at least 30 days written "
            "notice of cancellation, as required by the Texas Insurance Code."
        ),
    ),
    dict(
        doc_id="ho_am_tx_2024", title="Texas Amendatory Endorsement",
        form="HO 01 42", edition="2024", status="active", jurisdiction="TX",
        doc_type="endorsement", policy_type="homeowners",
        amends="ho3_tx_2024",
        section_path="Paragraph C > Water Damage",
        clause_type="endorsement_change", acl_roles=["agent_personal", "underwriter"],
        text=(
            "Paragraph 'Water Damage' of SECTION I Exclusions is amended: in Texas, "
            "coverage for sudden and accidental water discharge includes resulting mold "
            "remediation up to $5,000 unless a higher limit is shown in the Declarations."
        ),
    ),

    # -------- FL amendatory endorsement (different jurisdiction) -------
    dict(
        doc_id="ho_am_fl_2024", title="Florida Amendatory Endorsement",
        form="HO 01 09", edition="2024", status="active", jurisdiction="FL",
        doc_type="endorsement", policy_type="homeowners",
        section_path="Paragraph A > Hurricane Deductible",
        clause_type="endorsement_change", acl_roles=["agent_personal", "underwriter"],
        text=(
            "Florida Amendatory Endorsement. A separate hurricane deductible of 2% of "
            "Coverage A applies to loss caused by a hurricane declared by the National "
            "Hurricane Center, in place of the all-perils deductible."
        ),
    ),

    # --------------- DP-3 Texas (for comparison queries) ---------------
    dict(
        doc_id="dp3_tx_2024", title="Dwelling Property 3 — Special Form (Texas)",
        form="DP 00 03", edition="2024", status="active", jurisdiction="TX",
        doc_type="policy_form", policy_type="dwelling_fire",
        section_path="SECTION I > Exclusions > Water Damage",
        clause_type="exclusion", acl_roles=["agent_personal", "underwriter"],
        text=(
            "DP-3 Water Damage Exclusion. We do not insure for loss caused by flood, "
            "surface water, tidal water, or water that backs up through sewers or drains. "
            "Unlike the homeowners form, the DP-3 provides no coverage for mold "
            "remediation from covered water discharge, and sudden and accidental "
            "discharge coverage applies only if the dwelling was occupied within 30 days "
            "before the loss."
        ),
    ),

    # ------------- Commercial auto (commercial ACL only) ---------------
    dict(
        doc_id="ca_hnoa_2024", title="Hired and Non-Owned Auto Liability Endorsement",
        form="CA 20 54", edition="2024", status="active", jurisdiction="US",
        doc_type="endorsement", policy_type="commercial_auto",
        section_path="Coverage > Hired and Non-Owned Auto Liability",
        clause_type="coverage_grant", acl_roles=["agent_commercial", "underwriter"],
        text=(
            "Hired and Non-Owned Auto Liability (HNOA), form CA 20 54. A commercial auto "
            "policy may be extended to cover liability arising from hired autos (covered "
            "auto symbol 8) and non-owned autos (covered auto symbol 9), including "
            "employees' personal vehicles used in the insured's business. HNOA provides "
            "liability coverage only; it does not provide physical damage coverage for "
            "the hired or non-owned vehicle itself. To add HNOA, symbols 8 and 9 must be "
            "shown in Item Two of the declarations for Covered Autos Liability."
        ),
    ),

    # -------------------- Claims procedure -----------------------------
    dict(
        doc_id="claims_water_2025", title="Claims Procedure Manual — Water Damage Claims",
        form="CPM-WD", edition="2025", status="active", jurisdiction="US",
        doc_type="claims_procedure", policy_type="homeowners",
        section_path="Chapter 4 > Required Documentation",
        clause_type="procedure", acl_roles=["agent_personal", "agent_commercial", "claims", "underwriter"],
        text=(
            "Required documentation for a water damage claim: (1) completed First Notice "
            "of Loss form; (2) date-stamped photographs or video of the damage and the "
            "water source; (3) plumber's or contractor's report identifying the cause; "
            "(4) itemized repair estimate; (5) receipts or proof of ownership for damaged "
            "personal property; (6) mitigation invoices (water extraction, drying) — "
            "policyholders must mitigate further damage; and (7) for sewer backup claims, "
            "confirmation whether the optional water backup endorsement is on the policy. "
            "Claims should be reported within 30 days of discovery."
        ),
    ),

    # ------------------ Underwriting guideline -------------------------
    dict(
        doc_id="uw_hvh_2025", title="Underwriting Guideline — High-Value Homes",
        form="UWG-12", edition="2025", status="active", jurisdiction="US",
        doc_type="uw_guideline", policy_type="homeowners",
        section_path="Section 3 > Eligibility and Referral Rules",
        clause_type="procedure", acl_roles=["underwriter"],
        text=(
            "High-value homes (Coverage A limit above $1,500,000) require: a full "
            "interior and exterior inspection within 60 days of binding; central station "
            "fire and burglar alarm; and replacement cost documentation (appraisal or "
            "builder contract). Homes above $3,000,000, homes with unrepaired prior "
            "losses, or coastal Tier 1 locations must be referred to a senior underwriter "
            "before quoting. Wildfire zone scores of 8 or higher are outside appetite."
        ),
    ),

    # --------------------------- FAQ -----------------------------------
    dict(
        doc_id="faq_flood_2025", title="Agent FAQ — Flood and Water Coverage",
        form="FAQ-7", edition="2025", status="active", jurisdiction="US",
        doc_type="faq", policy_type="homeowners",
        section_path="Q3 > Is flood covered under a homeowners policy?",
        clause_type="faq", acl_roles=["agent_personal", "agent_commercial", "claims", "underwriter"],
        text=(
            "Q: Is flood covered under a homeowners policy? A: No. Flood, surface water, "
            "and storm surge are excluded under both homeowners (HO-3) and dwelling "
            "(DP-3) forms. Flood coverage must be written separately through the National "
            "Flood Insurance Program (NFIP) or a private flood market. An optional water "
            "backup endorsement can be added for sewer and drain backup, which is "
            "different from flood."
        ),
    ),
]
