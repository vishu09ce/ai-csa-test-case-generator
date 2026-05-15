FEW_SHOT_EXAMPLES = """\
--- FEW-SHOT EXAMPLES ---
The following four examples demonstrate the required output standard. \
Study them before generating your response.

EXAMPLE 1 — High Process Risk, clear requirement, single acceptance criterion
Teaches: complete scripted test case standard. High confidence. No flags.

INPUT:
Requirement ID: REQ-031
Source Document: FRS
Section: 7.2 Record Approval and Closure
Requirement Text: The system shall lock the verified record upon approver confirmation and update the record status to Approved.
Intended Use: This feature is intended to provide the Approver with tools to make a formal approval decision resulting in a permanently locked, immutable approved record.
Risk Classification: High Process Risk
Risk Rationale: Failure could produce an incorrectly approved or unlocked record — directly compromising the integrity of the quality record.
FRS Specification: On Approver confirmation the system shall: (1) set the verified record to read-only; (2) update status from Submitted for Approval to Approved; (3) record approver name, initials, and timestamp in the activity log; (4) make the approved record available for export.
Acceptance Criteria: Verified record is uneditable after approval. Status displays Approved. Activity log contains an Approved event with approver identity and timestamp.

OUTPUT:
{"tc_id":"TC-031","req_id":"REQ-031","iu_ref":"IU-009","risk_class":"High Process Risk","preconditions":["User is logged in with Approver role","Record RECORD-TEST-001 is in Submitted for Approval state","All review fields in the verified record are completed"],"test_steps":["Navigate to the Approval Queue","Locate record RECORD-TEST-001","Verify the verified record is displayed in read-only view","Click the Approve button","Enter full name in the Name field","Enter initials in the Initials field","Enter today's date in the Date field","Click Confirm Approval"],"expected_result":"System locks the verified record — all fields become uneditable. Record status updates from Submitted for Approval to Approved. Activity log records an Approved event capturing approver name, initials, and timestamp. Approved record becomes available for export.","actual_result":"","pass_fail":"","confidence":"High","flags":[]}

---

EXAMPLE 2 — High Process Risk, complex requirement, multiple acceptance criteria
Teaches: multi-criteria decomposition into separate test cases. MULTI_ACCEPTANCE_CRITERIA flag.

INPUT:
Requirement ID: REQ-015
Source Document: FRS
Section: 5.3 Confidence Classification
Requirement Text: The system shall assign a confidence tier to each extracted item and flag items requiring human review.
Risk Classification: High Process Risk
Risk Rationale: Failure could misdirect reviewer effort causing uncertain items to proceed without adequate human review.
FRS Specification: Assign one of three confidence tiers: High, Medium, Low. Medium and Low items shall be flagged for mandatory reviewer attention. Flags shall persist until explicitly actioned.
Acceptance Criteria: AC-1: Each extracted item displays its assigned confidence tier. AC-2: Medium and Low items are visually distinguished from High items. AC-3: Flags on Medium and Low items prevent submission until explicitly actioned.

OUTPUT:
[{"tc_id":"TC-015a","req_id":"REQ-015","iu_ref":"IU-005","risk_class":"High Process Risk","preconditions":["User is logged in with Reviewer role","Record contains items with High, Medium, and Low confidence tiers"],"test_steps":["Navigate to the Review Interface","Locate the extracted items list","Verify each item displays a confidence tier label"],"expected_result":"Every extracted item displays a confidence tier label — High, Medium, or Low. No item is displayed without a confidence tier.","actual_result":"","pass_fail":"","confidence":"High","flags":["MULTI_ACCEPTANCE_CRITERIA"]},{"tc_id":"TC-015b","req_id":"REQ-015","iu_ref":"IU-005","risk_class":"High Process Risk","preconditions":["Record contains at least one High, one Medium, and one Low confidence item"],"test_steps":["Navigate to the Review Interface","Locate a High confidence item and note its visual presentation","Locate a Medium confidence item and verify it is visually distinct","Locate a Low confidence item and verify it is visually distinct from both"],"expected_result":"Medium and Low confidence items are visually distinguished from High confidence items through a consistent visual indicator. The distinction is immediately apparent without additional navigation.","actual_result":"","pass_fail":"","confidence":"High","flags":["MULTI_ACCEPTANCE_CRITERIA"]},{"tc_id":"TC-015c","req_id":"REQ-015","iu_ref":"IU-005","risk_class":"High Process Risk","preconditions":["Record contains at least one unactioned Medium or Low confidence item"],"test_steps":["Leave at least one Medium or Low confidence item unactioned","Click the Submit button"],"expected_result":"System prevents submission and displays a specific message identifying the unactioned items that must be resolved before submission is permitted.","actual_result":"","pass_fail":"","confidence":"High","flags":["MULTI_ACCEPTANCE_CRITERIA"]}]

---

EXAMPLE 3 — Not High Process Risk, exploratory scenario
Teaches: UTR output structure. Three scenario types. Observations and conclusion blank.

INPUT:
Requirement ID: REQ-004
Source Document: URS
Section: 3.1 Record Library Management
Requirement Text: The system shall allow users to search and filter the record library by title, number, status, and date.
Risk Classification: Not High Process Risk
Risk Rationale: Failure affects discoverability but does not compromise record integrity or approval status.
FRS Specification: Record list supports search by title (partial match) and filter by status and date range. Results update in real time.

OUTPUT:
{"utr_id":"UTR-004","req_id":"REQ-004","iu_ref":"IU-004","risk_class":"Not High Process Risk","feature_description":"Record library search and filter — partial title match, status filter, date filter, real-time results.","exploratory_scenarios":["Normal use: Enter a partial title that matches multiple records — verify all matching records are returned and non-matching records are excluded. Apply a status filter while the search is active — verify results reflect both the search term and the filter simultaneously.","Boundary condition: Enter a single character as the search term — verify the system returns all records containing that character without error. Enter the maximum permitted character count in the search field — verify the system accepts the input and returns results.","Error state: Enter a search term that matches no records — verify the system displays a specific no-results message rather than an empty list with no explanation. Clear the search field and verify the full record list is restored."],"tester_observations":"","conclusion":"","confidence":"High","flags":[]}

---

EXAMPLE 4 — Ambiguous requirement, low confidence
Teaches: low confidence flagging. Return structured JSON with specific flags. Never fabricate.

INPUT:
Requirement ID: REQ-022
Source Document: URS
Section: 4.2 Extraction Performance
Requirement Text: The system shall extract eligibility criteria from documents with high accuracy.
Risk Classification: High Process Risk
FRS Specification: No specific accuracy threshold or measurement method defined in FRS.
Acceptance Criteria: Not defined in source documents.

OUTPUT:
{"tc_id":"TC-022","req_id":"REQ-022","iu_ref":"","risk_class":"High Process Risk","preconditions":[],"test_steps":[],"expected_result":"","actual_result":"","pass_fail":"","confidence":"Low","flags":["AMBIGUOUS_REQUIREMENT: 'High accuracy' is not a testable criterion — no accuracy threshold is defined in the URS or FRS. A specific measurable threshold is required before a test case can be generated.","MISSING_FRS_SPEC: No FRS specification found for the accuracy measurement method.","MISSING_ACCEPTANCE_CRITERIA: No acceptance criteria defined for REQ-022 in FRS or BRD.","BOUNDARY_NOT_DEFINED: No numeric threshold or measurement methodology defined for 'high accuracy'."]}

--- END OF EXAMPLES ---
"""
