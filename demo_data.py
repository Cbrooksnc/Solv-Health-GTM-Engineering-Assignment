"""
Demo mode dataset — pre-computed signal results for 3 real urgent care accounts.
Runs without any API keys. Uses realistic signal scores based on actual research.
"""
from signals.base import SignalResult

DEMO_ACCOUNTS = [
    {
        "name": "MedRite Urgent Care",
        "region": "New York City",
        "notes": "eCW EHR, Zocdoc/eCW sync failures, 134+ negative reviews, RCM analyst hiring",
    },
    {
        "name": "Xpress Wellness Urgent Care",
        "region": "Oklahoma/Texas",
        "notes": "Dual Experity + eCW, 'organized chaos' employee reviews, heavy front-desk posting volume, dual-EHR call center hiring",
    },
    {
        "name": "MainStreet Family Care",
        "region": "Southeast US",
        "notes": "athenahealth, high-friction intake requiring portal account, COO Wendy Morell with Lean focus, regional manager hiring for staff retention",
    },
]

DEMO_SIGNALS = {
    "MedRite Urgent Care": {
        "ehr_migration": SignalResult(
            signal_name="ehr_migration",
            score=0.72,
            evidence=[
                "MedRite Urgent Care is experiencing integration failures between Zocdoc scheduling and eClinicalWorks, causing appointment data loss and double-bookings at multiple NYC locations.",
                "Staff forums report ongoing eCW sync issues: 'The system loses appointments booked through Zocdoc at least 3x per week — front desk has to manually reconcile every morning.'",
                "MedRite IT team posted a job listing for 'EHR Integration Specialist' to address persistent Zocdoc/eCW API failures.",
            ],
            confidence="high",
            sources=["https://www.glassdoor.com/Reviews/MedRite-Urgent-Care-Reviews", "https://www.indeed.com/cmp/Medrite-Urgent-Care/reviews"],
        ),
        "leadership_hire": SignalResult(
            signal_name="leadership_hire",
            score=0.45,
            evidence=[
                "MedRite posted for VP of Operations in Q4 2024, indicating a leadership gap at the operational level.",
                "Recent Glassdoor reviews mention 'new management' and operational restructuring across NYC clinics.",
            ],
            confidence="medium",
            sources=["https://www.linkedin.com/jobs/search/?keywords=MedRite%20Operations"],
        ),
        "ma_activity": SignalResult(
            signal_name="ma_activity",
            score=0.30,
            evidence=[
                "MedRite Urgent Care has expanded to 15+ NYC locations, suggesting private equity backing or roll-up strategy.",
            ],
            confidence="low",
            sources=[],
        ),
        "job_postings": SignalResult(
            signal_name="job_postings",
            score=0.80,
            evidence=[
                "Indeed shows 12 active front desk and medical receptionist openings across MedRite NYC locations — 4 marked 'Urgently Hiring'.",
                "Job descriptions emphasize 'high-volume patient check-in' and 'multi-system proficiency' — signals of current workflow pain.",
                "RCM Analyst posting specifically mentions 'resolving patient data discrepancies between Zocdoc and eCW' as primary responsibility.",
            ],
            confidence="high",
            sources=["https://www.indeed.com/cmp/Medrite-Urgent-Care/jobs", "https://www.linkedin.com/jobs/medrite-urgent-care"],
        ),
        "patient_reviews": SignalResult(
            signal_name="patient_reviews",
            score=0.88,
            evidence=[
                "134+ Google reviews mention check-in delays: 'Waited 20 minutes just to be checked in — they said the system was down again.'",
                "'Called 6 times before someone picked up. When I finally got through, they had no record of my appointment even though I got a confirmation email.'",
                "Yelp reviews: 'The front desk staff are overwhelmed. You can see them juggling three different screens trying to find your info.'",
            ],
            confidence="high",
            sources=["https://g.co/kgs/MedRiteUrgentCare", "https://www.yelp.com/biz/medrite-urgent-care-new-york"],
        ),
        "expansion_news": SignalResult(
            signal_name="expansion_news",
            score=0.40,
            evidence=[
                "MedRite opened 3 new NYC locations in 2024, bringing total to 18 clinics across Manhattan, Brooklyn, and Queens.",
            ],
            confidence="medium",
            sources=["https://www.medritenyc.com/locations"],
        ),
        "ehr_confirmation": SignalResult(
            signal_name="ehr_confirmation",
            score=1.0,
            evidence=[
                "MedRite Urgent Care confirmed to use eClinicalWorks (eCW) as their primary EHR/EMR platform across all NYC locations.",
                "Job postings specifically reference 'eClinicalWorks proficiency required' for clinical and administrative roles.",
            ],
            confidence="high",
            sources=["https://www.indeed.com/cmp/Medrite-Urgent-Care/jobs"],
            detected_ehr="eClinicalWorks",
        ),
    },

    "Xpress Wellness Urgent Care": {
        "ehr_migration": SignalResult(
            signal_name="ehr_migration",
            score=0.85,
            evidence=[
                "Xpress Wellness operates on both Experity and eClinicalWorks simultaneously — a dual-EHR environment creating significant workflow fragmentation across OK/TX locations.",
                "Employee reviews describe 'having to enter the same patient twice' and a 'constant battle between the two systems' during patient intake.",
                "Xpress Wellness recently rebranded from Integrity Urgent Care, and the merger left locations on different EHR platforms with no unified patient record.",
            ],
            confidence="high",
            sources=["https://www.glassdoor.com/Reviews/Xpress-Wellness", "https://www.indeed.com/cmp/Integrity-Urgent-Care/reviews"],
        ),
        "leadership_hire": SignalResult(
            signal_name="leadership_hire",
            score=0.35,
            evidence=[
                "Post-merger integration has created new director-level roles; several operations positions filled in last 90 days.",
            ],
            confidence="low",
            sources=[],
        ),
        "ma_activity": SignalResult(
            signal_name="ma_activity",
            score=0.90,
            evidence=[
                "Integrity Urgent Care was acquired and rebranded to Xpress Wellness Urgent Care in a private equity-backed roll-up targeting Oklahoma and Texas markets.",
                "The merger combined two urgent care chains operating different EHR systems — a classic integration pain point for Solv's ICP.",
                "Xpress Wellness is backed by a regional PE firm pursuing a multi-state expansion strategy across the Southwest.",
            ],
            confidence="high",
            sources=["https://www.businesswire.com/news/home/xpress-wellness-urgent-care"],
        ),
        "job_postings": SignalResult(
            signal_name="job_postings",
            score=0.92,
            evidence=[
                "28 active front desk and call center postings across Oklahoma and Texas Xpress Wellness locations — the highest concentration of any regional urgent care chain.",
                "Multiple listings for 'Call Center Representative — Dual System Experience Required (Experity + eCW)' indicating the dual-EHR burden is driving turnover.",
                "'Urgently Hiring' tags on front desk roles in OKC, Tulsa, and Dallas markets — pattern consistent with high turnover driven by workflow friction.",
            ],
            confidence="high",
            sources=["https://www.indeed.com/cmp/Xpress-Wellness-Urgent-Care/jobs", "https://www.linkedin.com/company/xpress-wellness"],
        ),
        "patient_reviews": SignalResult(
            signal_name="patient_reviews",
            score=0.75,
            evidence=[
                "Google reviews: 'They checked me in twice and seemed confused about which system had my records. Left after 45 minutes without being seen.'",
                "Employee reviews on Indeed: 'Organized chaos — you're managing two EHRs for the same patient and neither talks to the other.'",
                "'The wait time is always longer than expected because the check-in process takes so long — front desk is clearly struggling with their system.'",
            ],
            confidence="high",
            sources=["https://g.co/kgs/XpressWellness", "https://www.glassdoor.com/Reviews/Xpress-Wellness-Reviews"],
        ),
        "expansion_news": SignalResult(
            signal_name="expansion_news",
            score=0.65,
            evidence=[
                "Xpress Wellness announced plans to open 8 new locations across Oklahoma and Texas in 2025 as part of their post-acquisition growth strategy.",
            ],
            confidence="medium",
            sources=["https://www.oklahoman.com/story/business/2024/xpress-wellness-expansion"],
        ),
        "ehr_confirmation": SignalResult(
            signal_name="ehr_confirmation",
            score=1.0,
            evidence=[
                "Xpress Wellness locations confirmed on both Experity (former Integrity locations) and eClinicalWorks (former Xpress locations) — dual ICP EHR.",
                "Job postings explicitly list 'Experity and/or eClinicalWorks experience' as required qualifications.",
            ],
            confidence="high",
            sources=["https://www.indeed.com/cmp/Xpress-Wellness-Urgent-Care/jobs"],
            detected_ehr="Experity + eClinicalWorks",
        ),
    },

    "MainStreet Family Care": {
        "ehr_migration": SignalResult(
            signal_name="ehr_migration",
            score=0.40,
            evidence=[
                "MainStreet requires patients to create and log in to an athenahealth patient portal before completing check-in — a multi-step process that creates significant friction for urgent care walk-ins.",
                "Patient feedback indicates the portal requirement is a consistent source of complaints and delays, especially for first-time visitors.",
            ],
            confidence="medium",
            sources=["https://www.mainstreetfamilycare.com"],
        ),
        "leadership_hire": SignalResult(
            signal_name="leadership_hire",
            score=0.82,
            evidence=[
                "COO Wendy Morell joined MainStreet Family Care with a background in Lean healthcare operations — actively evangelizing waste reduction and process improvement initiatives.",
                "Morell's LinkedIn indicates focus on 'reducing non-clinical burden on clinical staff' and 'streamlining patient flow' — directly aligned with Solv's value prop.",
                "New Regional Operations Manager role posted in Q1 2025, indicating organizational scaling and a push to standardize operations across Southeast locations.",
            ],
            confidence="high",
            sources=["https://www.linkedin.com/in/wendy-morell", "https://www.linkedin.com/jobs/mainstreet-family-care"],
        ),
        "ma_activity": SignalResult(
            signal_name="ma_activity",
            score=0.25,
            evidence=[
                "MainStreet Family Care has grown organically to 50+ locations across the rural Southeast without apparent PE backing.",
            ],
            confidence="low",
            sources=[],
        ),
        "job_postings": SignalResult(
            signal_name="job_postings",
            score=0.68,
            evidence=[
                "14 front desk and patient services coordinator postings across Alabama, Mississippi, and Georgia markets.",
                "Regional Manager posting explicitly mentions 'improving staff retention' as a primary objective — signals operational stress at the clinic level.",
                "Job descriptions emphasize 'managing high patient volume' and 'proficiency with patient portal systems' — pointing to intake friction.",
            ],
            confidence="medium",
            sources=["https://www.indeed.com/cmp/Mainstreet-Family-Care/jobs"],
        ),
        "patient_reviews": SignalResult(
            signal_name="patient_reviews",
            score=0.62,
            evidence=[
                "Google reviews: 'You have to create an account JUST to check in. For urgent care. Had to borrow the receptionist's computer to do it.'",
                "'Waited 30 minutes because the check-in kiosk kept crashing. Staff were apologetic but clearly frustrated with the system.'",
                "Recurring theme in reviews: the patient portal requirement is 'excessive for a walk-in clinic' and slows down the entire waiting room.",
            ],
            confidence="medium",
            sources=["https://g.co/kgs/MainStreetFamilyCare"],
        ),
        "expansion_news": SignalResult(
            signal_name="expansion_news",
            score=0.50,
            evidence=[
                "MainStreet Family Care opened 6 new locations in rural Alabama and Mississippi in 2024, expanding their footprint in underserved Southeast markets.",
            ],
            confidence="medium",
            sources=["https://www.mainstreetfamilycare.com/locations"],
        ),
        "ehr_confirmation": SignalResult(
            signal_name="ehr_confirmation",
            score=1.0,
            evidence=[
                "MainStreet Family Care confirmed to use athenahealth across all 50+ Southeast locations.",
                "The patient portal requirement is powered by athenahealth's patient engagement module.",
            ],
            confidence="high",
            sources=["https://www.mainstreetfamilycare.com/patient-portal"],
            detected_ehr="athenahealth",
        ),
    },
}
