from enum import Enum

class GrievanceCategory(str, Enum):
    SYSTEM_PORTAL_ISSUES = "system_portal_issues"
    DEPARTMENTAL_PROCESS_DELAYS = "departmental_process_delays"
    SYSTEM_DEPARTMENT_COORDINATION_ISSUES = "system_department_coordination_issues"
    INFORMATION_AND_COMMUNICATION_GAPS = "information_and_communication_gaps"
    GOVERNANCE_POLICY_LEVEL_ISSUES = "governance_policy_level_issues"
    UNCLASSIFIED = "unclassified"
