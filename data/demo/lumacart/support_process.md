# LumaCart Commerce support processes

LumaCart is a fictional ecommerce support operation. Requests arrive through chat, email, web form, and phone. Agents validate the order or account reference, classify the request, follow category procedures, and route risk-sensitive exceptions for human review.

## Order tracking

- **Standard workflow:** Verify the order reference, retrieve fulfillment and carrier status, select the approved status response, and send it for straightforward cases.
- **Systems used:** Support workspace, order management system, and carrier tracking portal.
- **Human review:** Required for conflicting carrier events, lost-package indicators, or repeated delivery failures.
- **Exceptions:** Split shipments, backorders, stale tracking events, and invalid order references.

## Return request

- **Standard workflow:** Verify order eligibility, review the return window and item rules, prepare authorization instructions, and route exceptions.
- **Systems used:** Support workspace, order management system, and returns portal.
- **Human review:** Required for policy exceptions, high-value items, or disputed condition.
- **Exceptions:** Final-sale items, bundled products, expired windows, partial quantities, and missing order references.

## Refund status

- **Standard workflow:** Verify the return or cancellation reference, retrieve the recorded refund state, and communicate the documented processing status.
- **Systems used:** Support workspace, returns portal, and payment-status view.
- **Human review:** Required when payment status conflicts with the order record or an adjustment is requested.
- **Exceptions:** Split tenders, failed payment reversals, unreceived returns, and disputed refund amounts.

## Account access

- **Standard workflow:** Verify the shopper, check account state, trigger the approved reset or unlock workflow, and provide standard access steps.
- **Systems used:** Support workspace and account administration console.
- **Human review:** Required for identity mismatches, suspected compromise, or repeated lockouts.
- **Exceptions:** Changed email address, merged accounts, inactive accounts, and failed verification.

## Promotion question

- **Standard workflow:** Identify the campaign, review current terms, compare cart eligibility, and explain the documented rule or route an exception.
- **Systems used:** Support workspace, campaign reference library, and order view.
- **Human review:** Required for conflicting campaign rules or discretionary adjustments.
- **Exceptions:** Stacked promotions, region restrictions, expired campaigns, item exclusions, and campaign-specific overrides.

## Subscription change

- **Standard workflow:** Verify the account, review subscription state and allowed changes, prepare the requested change, and obtain approval where required.
- **Systems used:** Support workspace and subscription administration portal.
- **Human review:** Required for disputed charges, retroactive changes, or account-verification failures.
- **Exceptions:** Already-shipped renewals, bundled subscriptions, payment failure, and paused-account limits.

## Fraud review

- **Standard workflow:** Capture the reference, preserve the account state, and route the case to the authorized risk team without making a disposition.
- **Systems used:** Support workspace and restricted risk-review queue.
- **Human review:** Mandatory for every case; support agents cannot approve transactions, remove restrictions, or override risk decisions.
- **Exceptions:** Identity mismatch, disputed ownership, repeated high-risk activity, and incomplete verification.

## Product question

- **Standard workflow:** Identify the product and intended use, search published specifications, provide documented information, or route uncertain compatibility questions.
- **Systems used:** Support workspace, product catalog, and knowledge base.
- **Human review:** Required for undocumented compatibility, safety-sensitive uses, or unavailable specifications.
- **Exceptions:** Marketplace items, discontinued products, regional variants, and subjective recommendations.

## Known limitations

The documentation does not establish integration APIs, detailed permission scopes, campaign exception frequency, refund authority, security approval, or implementation readiness. Those facts require stakeholder clarification.
