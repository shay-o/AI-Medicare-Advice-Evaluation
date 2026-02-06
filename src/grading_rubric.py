"""
Grading rubric mapping for SHIP study evaluation.
Maps questions to scoring criteria from eAppendix 4.
"""

from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel


class ScoreCategory(str, Enum):
    """Score categories from SHIP study rubric."""
    ACCURATE_COMPLETE = "accurate_complete"
    SUBSTANTIVE_INCOMPLETE = "substantive_incomplete"
    NOT_SUBSTANTIVE = "not_substantive"
    INCORRECT = "incorrect"
    MISSING = "missing"


class QuestionGroup(BaseModel):
    """Represents a question group from the rubric."""
    group_id: str
    group_name: str
    scenario: str  # "medicare_only", "dual_eligible", or "both"
    question_numbers: List[int]
    topic: str
    accurate_complete_criteria: List[str]
    substantive_incomplete_criteria: List[str]
    not_substantive_criteria: List[str]
    incorrect_criteria: List[str]


# Question Group 1: Both Scenarios - Enrollment Timing
QUESTION_GROUP_1 = QuestionGroup(
    group_id="QG1",
    group_name="Timing for Initial Medicare Enrollment & Subsequent Changes",
    scenario="both",
    question_numbers=[1],
    topic="When can I select my Medicare coverage plan, and when can I change it later?",
    accurate_complete_criteria=[
        "Mentioned that you can enroll in Medicare/select coverage within 3 months of turning 65",
        "Substantively answered the 'when can I change it' question by referencing open enrollment period, annual election period, or special enrollment periods"
    ],
    substantive_incomplete_criteria=[
        "Some substantive information was provided but both components of the question were not answered",
        "Said shopper can enroll 'now' (because within 3 months) but did not address when changes can be made"
    ],
    not_substantive_criteria=[
        "Counselor did not answer the question",
        "Said they did not know",
        "Declined to answer without shopper's Medicare card"
    ],
    incorrect_criteria=[
        "Incorrect information was provided that was substantive enough to materially change the substance of the answer or affect an enrollee's decision"
    ]
)

# Question Group 2: Both Scenarios - Spanish Translation Services
QUESTION_GROUP_2 = QuestionGroup(
    group_id="QG2",
    group_name="Availability of Spanish Translation Services",
    scenario="both",
    question_numbers=[16],  # Q16 for Medicare-Only, Q8 for Dual-Eligible
    topic="Do you offer Spanish translation services at your location?",
    accurate_complete_criteria=[
        "Substantively said yes to Spanish translation services being available"
    ],
    substantive_incomplete_criteria=[],
    not_substantive_criteria=[
        "Said no, even if they offered a workaround or a way to provide some degree of translation services",
        "Counselor did not know"
    ],
    incorrect_criteria=[]
)

# Question Group 9: Medicare-Only - Employer Plan Interaction
QUESTION_GROUP_9 = QuestionGroup(
    group_id="QG9",
    group_name="Medicare Enrollment & Interaction with Employer Plan",
    scenario="medicare_only",
    question_numbers=[2],
    topic="Do I have to sign up for Medicare when I turn 65, or can I remain on my employer plan?",
    accurate_complete_criteria=[
        "Counselor's answer substantively makes clear that shopper is not required to enroll in Medicare and can keep their employer plan",
        "Also discusses Part B implications (e.g., mentions possible late enrollment penalty)"
    ],
    substantive_incomplete_criteria=[
        "Counselor says that the shopper can remain on employer plan and is not required to enroll in Medicare but does not discuss Part B/late enrollment penalty implications",
        "Says that shopper is not required to enroll in Medicare without elaborating"
    ],
    not_substantive_criteria=[
        "Counselor said they do not know or otherwise did not substantively answer the question"
    ],
    incorrect_criteria=[
        "Counselor said that the shopper would be automatically enrolled in Medicare",
        "Said shopper is required to enroll in Medicare"
    ]
)

# Question Group 10: Medicare-Only - Traditional Medicare vs Medicare Advantage
QUESTION_GROUP_10 = QuestionGroup(
    group_id="QG10",
    group_name="Considerations for Choosing Traditional Medicare vs Medicare Advantage",
    scenario="medicare_only",
    question_numbers=[3],
    topic="How are Medicare Advantage Plans different from regular Medicare, and what are good and bad about them?",
    accurate_complete_criteria=[
        "Medicare Advantage: May have lower premiums, deductibles, and cost sharing than traditional Medicare plus Supplement plan",
        "Medicare Advantage: Has a more restrictive choice of providers and hospitals",
        "Medicare Advantage: You may not be able to keep your doctor",
        "Medicare Advantage: Covers all Medicare Part A and Part B (sometimes Part D) benefits",
        "Medicare Advantage: One must continue to pay the Medicare Part B premium in addition to their Medicare Advantage Plan premium",
        "Medicare Advantage: Often offers additional benefits such as vision, hearing, dental, fitness, grocery, OTC card, etc.",
        "Original Medicare: You automatically enroll in Medicare Part A when you apply for Medicare, which provides coverage for hospital stay",
        "Original Medicare: You have the option to enroll in Medicare Part B to cover doctors' services, outpatient care, and preventative services",
        "Original Medicare: Part A has a deductible and some cost sharing but no monthly premium",
        "Original Medicare: Part B has a monthly premium, some cost sharing, and a small deductible",
        "Original Medicare: Premiums and cost sharing can be more expensive than with Medicare Advantage Plans",
        "Original Medicare: Your choice of almost any provider, hospital, etc.",
        "Original Medicare: In order to receive coverage for prescription drugs, you must obtain a separate Prescription Drug Plan (Part D)",
        "Original Medicare: Can be paired with a Medigap/Medicare Supplement policy to reduce premiums, deductibles, and cost sharing"
    ],
    substantive_incomplete_criteria=[
        "Some (but not all) of the Medicare Advantage or Original Medicare topics were substantively covered"
    ],
    not_substantive_criteria=[
        "None of the Medicare Advantage or Original Medicare topics were substantively discussed",
        "Counselor said they do not know",
        "Otherwise did not substantively answer the question"
    ],
    incorrect_criteria=[
        "Incorrect information was provided that was substantive enough to materially change the substance of the answer or affect an enrollee's coverage decision"
    ]
)

# Question Group 11: Medicare-Only - Medicare Supplement Plans
QUESTION_GROUP_11 = QuestionGroup(
    group_id="QG11",
    group_name="Considerations for Medicare Supplement Plans",
    scenario="medicare_only",
    question_numbers=[4],
    topic="What is a Medicare Supplement Plan, how much do they cost, and when do I enroll?",
    accurate_complete_criteria=[
        "Supplement plans can be purchased separately if you choose traditional Medicare to help cover out-of-pocket costs",
        "All supplement plans cover Part A and Part B copays and hospital and hospice costs",
        "Some supplement plans cover Part A and Part B deductibles",
        "Some supplement plans have out-of-pocket limits",
        "Supplement plan costs vary based on how much is covered but usually range from $50-$300 per month",
        "You can enroll in a Supplement plan at any time",
        "You will get better rates if you enroll during your open enrollment period (which begins the day you turn 65 and lasts for six months afterwards)"
    ],
    substantive_incomplete_criteria=[
        "Some (but not all) of the Medicare Supplement Plan topics were substantively discussed"
    ],
    not_substantive_criteria=[
        "None of the Medicare Supplement Plan topics were substantively discussed",
        "Counselor said they do not know",
        "Otherwise did not substantively answer the question"
    ],
    incorrect_criteria=[
        "Incorrect information was provided that was substantive enough to materially change the substance of the answer or affect an enrollee's coverage decision"
    ]
)

# Question Group 12: Medicare-Only - Long-Term Care Coverage
QUESTION_GROUP_12 = QuestionGroup(
    group_id="QG12",
    group_name="Coverage of Long-Term Care",
    scenario="medicare_only",
    question_numbers=[5],
    topic="Do either original Medicare, Medicare Advantage Plans, or Medicare Supplement Plans cover long-term care?",
    accurate_complete_criteria=[
        "In general, none of these cover long-term care",
        "Although some time-limited nursing facility stays or in-home services may be covered",
        "OR: None of these provide coverage for long-term care"
    ],
    substantive_incomplete_criteria=[
        "Some, but not all relevant information was provided",
        "Accurately raised the limited Medicare coverage that may be provided in certain situations that is similar to long-term care without clarifying that Medicare does not actually cover long-term care"
    ],
    not_substantive_criteria=[
        "Counselor said they do not know or otherwise did not substantively answer the question"
    ],
    incorrect_criteria=[
        "Said that Medicare does cover long-term care without elaborating on the limited circumstances that apply"
    ]
)

# Question Group 13: Medicare-Only - Prescription Drug Coverage Options
QUESTION_GROUP_13 = QuestionGroup(
    group_id="QG13",
    group_name="Considerations for Prescription Drug Coverage",
    scenario="medicare_only",
    question_numbers=[6],
    topic="What are my options for Medicare prescription drug coverage, and how should I choose?",
    accurate_complete_criteria=[
        "You can choose either a Medicare Advantage Plan that covers prescription drugs or a stand-alone Part D plan",
        "Most Medicare Advantage options include prescription drug (Part D) coverage",
        "If you choose original Medicare, you could purchase a separate prescription drug (Part D) plan",
        "Each plan has a different list of covered drugs, and you would choose based on the medicine you take",
        "Each plan has different out-of-pocket costs for different drugs, and you would choose based on the medicine you take and your comfort with costs"
    ],
    substantive_incomplete_criteria=[
        "Some (but not all) of the prescription drug coverage considerations were substantively discussed"
    ],
    not_substantive_criteria=[
        "None of the prescription drug coverage considerations were substantively discussed",
        "Counselor said they do not know",
        "Otherwise did not substantively answer the question"
    ],
    incorrect_criteria=[
        "Incorrect information was provided that was substantive enough to materially change the substance of the answer or affect an enrollee's coverage decision"
    ]
)

# Question Group 14: Medicare-Only - Specific Plan Network
QUESTION_GROUP_14 = QuestionGroup(
    group_id="QG14",
    group_name="Ability to Determine if Specific PCP is in Network for Specific Plan",
    scenario="medicare_only",
    question_numbers=[7],
    topic="Can you tell me if [doctor name] is in the network for [plan name]?",
    accurate_complete_criteria=[
        "The doctor is confirmed to be in the network (or not in network with accurate information)"
    ],
    substantive_incomplete_criteria=[],
    not_substantive_criteria=[
        "Counselor did not provide a clear answer about network status"
    ],
    incorrect_criteria=[
        "Provided incorrect network status information"
    ]
)

# Question Group 15: Medicare-Only - Plan Premium
QUESTION_GROUP_15 = QuestionGroup(
    group_id="QG15",
    group_name="Ability to Determine Premium for Specific Plan",
    scenario="medicare_only",
    question_numbers=[8],
    topic="What is the monthly premium for [plan name]?",
    accurate_complete_criteria=[
        "Counselor provided the Plan premium and the Part B premium",
        "The amounts for each were accurate for the year in which the evaluation takes place"
    ],
    substantive_incomplete_criteria=[
        "Counselor only provided either the plan premium or the Part B premium (without clarifying that the plan premium was $0)",
        "Amount provided was accurate for the year",
        "OR: Provided an accurate range"
    ],
    not_substantive_criteria=[
        "Counselor did not provide an amount or range",
        "Said they do not know",
        "Otherwise did not substantively answer the question"
    ],
    incorrect_criteria=[
        "Counselor provided a dollar amount that was not accurate for the year",
        "Otherwise provided incorrect information which was substantive enough to materially change the answer or affect an enrollee's coverage decision"
    ]
)

# Question Group 16: Medicare-Only - Out-of-Network Care
QUESTION_GROUP_16 = QuestionGroup(
    group_id="QG16",
    group_name="Ability to Determine if Specific Plan Allows Out-of-Network Care",
    scenario="medicare_only",
    question_numbers=[9],
    topic="Would [plan name] let me go out of network?",
    accurate_complete_criteria=[
        "If PPO: Yes, and specified that there would be a higher cost or copay",
        "If HMO: No"
    ],
    substantive_incomplete_criteria=[
        "If PPO: Said yes but did not specify that the copay or cost would be higher",
        "OR: Did not say yes or no but said the copay or cost would be higher"
    ],
    not_substantive_criteria=[
        "Counselor said they do not know or otherwise did not substantively answer the question"
    ],
    incorrect_criteria=[
        "Provided wrong information about out-of-network coverage for the plan type"
    ]
)

# Question Group 17: Medicare-Only - In-Network PCP Copay
QUESTION_GROUP_17 = QuestionGroup(
    group_id="QG17",
    group_name="Knowledge of in-network PCP copay",
    scenario="medicare_only",
    question_numbers=[10],
    topic="What is the copay for a primary care doctor visit for [plan name]?",
    accurate_complete_criteria=[
        "Counselor said that the copay for an in-network PCP is $0 or that there is no copay"
    ],
    substantive_incomplete_criteria=[
        "Counselor made a general statement such as 'there is no copay for an HMO' or 'there is usually a $0 copay' without referencing the specific plan",
        "OR: Provided a dollar amount range that includes $0"
    ],
    not_substantive_criteria=[
        "Counselor said that they do not know or otherwise did not answer the question"
    ],
    incorrect_criteria=[
        "Counselor said a dollar amount other than $0",
        "OR: Provided a range that did not include $0"
    ]
)

# Question Group 18: Medicare-Only - Maximum Out-of-Pocket
QUESTION_GROUP_18 = QuestionGroup(
    group_id="QG18",
    group_name="Knowledge of maximum out-of-pocket limit",
    scenario="medicare_only",
    question_numbers=[12],
    topic="For [plan name], is there a limit on out-of-pocket costs I would have to pay each year?",
    accurate_complete_criteria=[
        "The dollar amount provided matches the amount in Medicare.gov plan finder tool for the year"
    ],
    substantive_incomplete_criteria=[
        "Counselor indicated there is a maximum but did not provide a dollar amount"
    ],
    not_substantive_criteria=[
        "Counselor did not answer the question"
    ],
    incorrect_criteria=[
        "The dollar amount provided does not match the amount in Medicare.gov plan finder tool for the year"
    ]
)

# Question Group 19: Medicare-Only - Prescription Drug Coverage Inclusion
QUESTION_GROUP_19 = QuestionGroup(
    group_id="QG19",
    group_name="Ability to determine if specific plan includes coverage for prescription drugs",
    scenario="medicare_only",
    question_numbers=[13],
    topic="Does [plan name] include prescription drug coverage?",
    accurate_complete_criteria=[
        "Counselor says yes (plan includes prescription drug coverage)"
    ],
    substantive_incomplete_criteria=[
        "Counselor provides a correct answer that is not specific to the plan being asked about",
        "Says they believe so or that most plans do",
        "OR: Says that the specific drugs are covered without clarifying that the plan includes prescription drug coverage more generally"
    ],
    not_substantive_criteria=[
        "Counselor said that they do not know or otherwise did not answer the question"
    ],
    incorrect_criteria=[
        "Counselor said no or otherwise provided incorrect information that was substantive enough to materially change the answer or affect an enrollee's coverage decision"
    ]
)

# Question Group 20: Medicare-Only - Specific Drug Coverage
QUESTION_GROUP_20 = QuestionGroup(
    group_id="QG20",
    group_name="Ability to determine if plan covers specific drug (Lipitor) and/or its generic equivalent",
    scenario="medicare_only",
    question_numbers=[14],
    topic="I take Lipitor. Is that covered by [plan name]?",
    accurate_complete_criteria=[
        "Counselor substantively said that Lipitor is not covered but a generic version is",
        "OR: Said that Lipitor is covered but a generic version is available at a lower cost"
    ],
    substantive_incomplete_criteria=[
        "Counselor said that Lipitor is covered without elaborating on cost or clarifying whether they were referring to Lipitor itself or its generic"
    ],
    not_substantive_criteria=[
        "Counselor said they did not know",
        "Said something to the effect that they thought so (without looking up the answer)",
        "Otherwise did not answer the question"
    ],
    incorrect_criteria=[
        "Counselor said that neither Lipitor nor its generic was covered"
    ]
)


# Create a mapping of question numbers to question groups
QUESTION_GROUPS_MEDICARE_ONLY = [
    QUESTION_GROUP_1,   # Q1
    QUESTION_GROUP_2,   # Q16
    QUESTION_GROUP_9,   # Q2
    QUESTION_GROUP_10,  # Q3
    QUESTION_GROUP_11,  # Q4
    QUESTION_GROUP_12,  # Q5
    QUESTION_GROUP_13,  # Q6
    QUESTION_GROUP_14,  # Q7
    QUESTION_GROUP_15,  # Q8
    QUESTION_GROUP_16,  # Q9
    QUESTION_GROUP_17,  # Q10
    QUESTION_GROUP_18,  # Q12
    QUESTION_GROUP_19,  # Q13
    QUESTION_GROUP_20,  # Q14
]

# ============================================================================
# Dual-Eligible Question Groups
# ============================================================================

# Question Group 21: Dual-Eligible Q2 - Medicare Enrollment Options with Medicaid
QUESTION_GROUP_21 = QuestionGroup(
    group_id="QG21",
    group_name="Medicare Enrollment Options for Dual-Eligible Beneficiaries",
    scenario="dual_eligible",
    question_numbers=[2],
    topic="What are my options for enrolling in Medicare coverage with full Medicaid?",
    accurate_complete_criteria=[
        "Mentioned can enroll in Original Medicare with Medicaid as secondary/supplemental coverage",
        "Mentioned can enroll in a D-SNP (Dual Special Needs Plan)",
        "Explained that Medicaid will help cover Medicare costs (premiums, deductibles, copays)",
        "Mentioned that D-SNPs integrate/coordinate Medicare and Medicaid benefits"
    ],
    substantive_incomplete_criteria=[
        "Mentioned D-SNP option but did not explain Medicaid cost-sharing assistance",
        "Mentioned Original Medicare option but did not mention D-SNP alternative",
        "Provided some substantive information but missed key details about integration"
    ],
    not_substantive_criteria=[
        "Counselor did not answer the question",
        "Said they did not know",
        "Only said 'you have options' without elaborating"
    ],
    incorrect_criteria=[
        "Said dual-eligible beneficiaries cannot enroll in Medicare Advantage",
        "Said Medicaid and Medicare cannot work together",
        "Provided materially incorrect information about enrollment options"
    ]
)

# Question Group 22: Dual-Eligible Q3 - D-SNP Enrollment Considerations
QUESTION_GROUP_22 = QuestionGroup(
    group_id="QG22",
    group_name="Considerations for D-SNP Enrollment Decision",
    scenario="dual_eligible",
    question_numbers=[3],
    topic="What should I consider when deciding whether to enroll in a D-SNP?",
    accurate_complete_criteria=[
        "Mentioned must use plan's network of providers (HMO/PPO restrictions)",
        "Mentioned may need to change doctors if current providers not in network",
        "Mentioned D-SNPs integrate Medicare and Medicaid benefits",
        "Mentioned care coordination/case management services",
        "Mentioned that Medicaid continues to cover cost-sharing",
        "Mentioned additional benefits may be available (dental, vision, etc.)",
        "Explained difference from Original Medicare in terms of provider choice"
    ],
    substantive_incomplete_criteria=[
        "Mentioned network restrictions but did not discuss care coordination benefits",
        "Mentioned integration but did not discuss potential provider changes",
        "Provided some considerations but missed key tradeoffs between flexibility and coordination"
    ],
    not_substantive_criteria=[
        "Counselor did not answer the question",
        "Said they did not know",
        "Only said 'it depends' without providing specific considerations"
    ],
    incorrect_criteria=[
        "Said D-SNPs do not have network restrictions",
        "Said cannot keep Medicaid if enrolled in D-SNP",
        "Provided materially incorrect information about D-SNP characteristics"
    ]
)

# Question Group 23: Dual-Eligible Q4 - D-SNP Availability
QUESTION_GROUP_23 = QuestionGroup(
    group_id="QG23",
    group_name="D-SNP Availability in Service Area",
    scenario="dual_eligible",
    question_numbers=[4],
    topic="Are there any D-SNPs available where I live?",
    accurate_complete_criteria=[
        "Directed shopper to Medicare.gov Plan Finder or similar tool",
        "Mentioned that D-SNP availability varies by county/ZIP code",
        "Offered to help look up plans or explained how to find them"
    ],
    substantive_incomplete_criteria=[
        "Said plans are available but did not direct to verification tool",
        "Mentioned checking online but did not specify Medicare.gov"
    ],
    not_substantive_criteria=[
        "Counselor did not know",
        "Said they cannot look up plan availability",
        "Did not provide actionable guidance"
    ],
    incorrect_criteria=[
        "Stated definitively that plans are/are not available without checking",
        "Provided incorrect information about how to find plans"
    ]
)

# Question Group 24: Dual-Eligible Q5 - Long-Term Care Coverage
QUESTION_GROUP_24 = QuestionGroup(
    group_id="QG24",
    group_name="Long-Term Care Coverage for Dual-Eligible Beneficiaries",
    scenario="dual_eligible",
    question_numbers=[5],
    topic="Do either regular Medicare, Medicare Advantage Plans, D-SNPs, or Medicaid cover long-term care?",
    accurate_complete_criteria=[
        "Stated that Medicare/MA generally do not cover long-term custodial care",
        "Mentioned that Medicaid may cover long-term care for eligible beneficiaries",
        "Explained difference between skilled nursing (Medicare) and custodial care (Medicaid)",
        "Mentioned that D-SNPs may help coordinate long-term care services through Medicaid"
    ],
    substantive_incomplete_criteria=[
        "Mentioned Medicare does not cover LTC but did not explain Medicaid coverage",
        "Mentioned Medicaid covers LTC but did not distinguish from Medicare's limited coverage",
        "Provided some accurate information but missed key distinctions"
    ],
    not_substantive_criteria=[
        "Counselor did not know",
        "Did not substantively answer the question",
        "Only said 'it depends' without explanation"
    ],
    incorrect_criteria=[
        "Said Medicare covers long-term custodial care",
        "Said Medicaid does not cover long-term care",
        "Confused skilled nursing with custodial care in a materially incorrect way"
    ]
)

# Question Group 25: Dual-Eligible Q6 - Medicaid Coverage of Medicare Costs
QUESTION_GROUP_25 = QuestionGroup(
    group_id="QG25",
    group_name="Medicaid Coverage of Medicare Premiums and Cost-Sharing",
    scenario="dual_eligible",
    question_numbers=[6],
    topic="Will Medicaid cover my Medicare premiums and cost-sharing?",
    accurate_complete_criteria=[
        "Stated that full Medicaid (or QMB Plus) covers Medicare Part B premium",
        "Stated that Medicaid covers Medicare cost-sharing (deductibles, copays, coinsurance)",
        "Mentioned that level of assistance depends on Medicaid eligibility category",
        "May have mentioned QMB (Qualified Medicare Beneficiary) program"
    ],
    substantive_incomplete_criteria=[
        "Mentioned premium coverage but not cost-sharing coverage (or vice versa)",
        "Said Medicaid helps with costs but did not specify what costs",
        "Provided partial information about coverage"
    ],
    not_substantive_criteria=[
        "Counselor did not know",
        "Did not answer the question",
        "Said 'maybe' or 'it depends' without further explanation"
    ],
    incorrect_criteria=[
        "Said Medicaid does not cover Medicare premiums or cost-sharing",
        "Said all Medicaid beneficiaries get the same level of assistance regardless of eligibility",
        "Provided materially incorrect information about coverage"
    ]
)

# Question Group 26: Dual-Eligible Q7 - Medicare Cost-Sharing Assistance Programs
QUESTION_GROUP_26 = QuestionGroup(
    group_id="QG26",
    group_name="Medicare Cost-Sharing Assistance Programs (Non-Full Medicaid)",
    scenario="dual_eligible",
    question_numbers=[7],
    topic="Are there programs that can help me pay for Medicare costs if I don't qualify for full Medicaid?",
    accurate_complete_criteria=[
        "Mentioned Medicare Savings Programs (QMB, SLMB, QI, or QDWI)",
        "Mentioned Extra Help/Low-Income Subsidy (LIS) for Part D prescription drugs",
        "Mentioned that these programs have income and asset limits",
        "Mentioned that these programs help with premiums, deductibles, or copays"
    ],
    substantive_incomplete_criteria=[
        "Mentioned Medicare Savings Programs but not Extra Help (or vice versa)",
        "Said programs exist but did not name specific programs",
        "Mentioned assistance but did not explain eligibility or what costs are covered"
    ],
    not_substantive_criteria=[
        "Counselor did not know",
        "Did not answer the question",
        "Only mentioned full Medicaid without discussing other programs"
    ],
    incorrect_criteria=[
        "Said no programs exist to help with Medicare costs",
        "Provided materially incorrect information about eligibility or benefits",
        "Confused these programs with other assistance programs"
    ]
)

# Dual-Eligible Question Groups List
QUESTION_GROUPS_DUAL_ELIGIBLE = [
    QUESTION_GROUP_1,   # Q1 (both scenarios)
    QUESTION_GROUP_21,  # Q2
    QUESTION_GROUP_22,  # Q3
    QUESTION_GROUP_23,  # Q4
    QUESTION_GROUP_24,  # Q5
    QUESTION_GROUP_25,  # Q6
    QUESTION_GROUP_26,  # Q7
    QUESTION_GROUP_2,   # Q8 (both scenarios)
]

# Map question numbers to question groups (Medicare-Only)
QUESTION_TO_GROUP_MAP_MO = {}
for group in QUESTION_GROUPS_MEDICARE_ONLY:
    for qnum in group.question_numbers:
        QUESTION_TO_GROUP_MAP_MO[qnum] = group

# Map question numbers to question groups (Dual-Eligible)
QUESTION_TO_GROUP_MAP_DE = {}
for group in QUESTION_GROUPS_DUAL_ELIGIBLE:
    for qnum in group.question_numbers:
        QUESTION_TO_GROUP_MAP_DE[qnum] = group

# Legacy map for backwards compatibility (defaults to Medicare-Only)
QUESTION_TO_GROUP_MAP = QUESTION_TO_GROUP_MAP_MO


def get_question_group(question_number: int, scenario: str = "medicare_only") -> QuestionGroup:
    """Get the question group for a given question number and scenario."""
    if scenario == "dual_eligible":
        return QUESTION_TO_GROUP_MAP_DE.get(question_number)
    else:
        return QUESTION_TO_GROUP_MAP_MO.get(question_number)


def get_all_question_groups(scenario: str = "medicare_only") -> List[QuestionGroup]:
    """Get all question groups for a scenario."""
    if scenario == "medicare_only":
        return QUESTION_GROUPS_MEDICARE_ONLY
    elif scenario == "dual_eligible":
        return QUESTION_GROUPS_DUAL_ELIGIBLE
    else:
        return []
