# HarborPoint Health Services administrative support processes

HarborPoint is a fictional administrative support center. It does not provide clinical advice or automate medical decisions. Requests arrive primarily by phone, web portal, email, and chat. Agents verify the service segment and request reference, classify the administrative issue, follow the documented workflow, and escalate exceptions to an authorized human team.

## Appointment scheduling

- **Standard workflow:** Verify the caller's administrative identifiers, review scheduling availability, propose eligible time options, and record the confirmed selection.
- **Systems used:** Support workspace and scheduling system.
- **Human review:** Required for conflicting restrictions, repeated failed verification, or requests outside published scheduling rules.
- **Exceptions:** Provider-template restrictions, unavailable appointment types, duplicate requests, and incomplete verification.

## Insurance eligibility

- **Standard workflow:** Verify administrative account details, review the available eligibility response, document the result, and route ambiguous results.
- **Systems used:** Support workspace and eligibility verification portal.
- **Human review:** Required when responses conflict, required fields are missing, or plan rules are unclear.
- **Exceptions:** Recently changed plans, employer-plan mismatches, incomplete responses, and unavailable verification data.

## Portal access

- **Standard workflow:** Verify the user, check account status, trigger the approved reset or unlock workflow, and provide standard access guidance.
- **Systems used:** Support workspace and portal administration console.
- **Human review:** Required for identity mismatches, repeated lockouts, or suspected account misuse.
- **Exceptions:** Changed contact information, duplicate accounts, inactive access, and failed verification.

## Billing question

- **Standard workflow:** Verify the statement reference, review posted administrative charges and payments, explain available information, and route disputed items.
- **Systems used:** Support workspace and billing administration system.
- **Human review:** Required for disputed balances, adjustment authority, or conflicting records.
- **Exceptions:** Unposted payments, coordination questions, adjustment requests, and missing statement references.

## Referral status

- **Standard workflow:** Verify the request reference, check receipt and routing status, communicate the documented status, and route missing or expired items.
- **Systems used:** Support workspace and referral administration queue.
- **Human review:** Required when documentation is incomplete or routing ownership is unclear.
- **Exceptions:** Missing paperwork, expired requests, duplicate referrals, and unavailable destination status.

## Prescription refill request

- **Standard workflow:** Verify the administrative request, capture the refill-routing information, and transfer it to the authorized licensed team without making a clinical decision.
- **Systems used:** Support workspace and licensed-team request queue.
- **Human review:** Mandatory for every request; support agents cannot approve, deny, or clinically evaluate refills.
- **Exceptions:** Urgent requests, incomplete verification, expired requests, and unavailable licensed-team routing.

## Medical records request

- **Standard workflow:** Verify identity requirements, provide the approved authorization instructions, check request status, and route completed documents to the records team.
- **Systems used:** Support workspace, secure records-request portal, and records queue.
- **Human review:** Required before release and whenever authorization is incomplete.
- **Exceptions:** Third-party requests, missing authorization, restricted delivery methods, and identity mismatch.

## General inquiry

- **Standard workflow:** Identify the administrative topic, collect missing context, determine ownership, and route the request.
- **Systems used:** Support workspace plus the destination team's approved system.
- **Human review:** Required whenever ownership, authority, or risk is unclear.
- **Exceptions:** Multi-topic requests, absent references, non-administrative questions, and requests outside published procedures.

## Known limitations

The documentation does not establish system API availability, detailed permission scopes, exception frequency, compliance approval status, or integration readiness. Those facts require stakeholder clarification before implementation planning.
