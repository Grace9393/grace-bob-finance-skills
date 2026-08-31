# AR Operations Taxonomy

Standard operational vocabulary for findings and recommendations. Adapted from the
community "commerce-accounts-receivable" skill (mcpmarket v1.0.0); its StateSet
iCommerce MCP tool bindings were removed — these tables are ERP-agnostic reference.

## Aging buckets and recommended actions

| Bucket | Days outstanding | Recommended action |
|--------|-----------------|--------------------|
| Current | Not yet due | No action |
| 1–30 days | 1–30 past due | Reminder1 (friendly reminder) |
| 31–60 days | 31–60 past due | Reminder2 (follow-up) |
| 61–90 days | 61–90 past due | Reminder3 (urgent notice) |
| 90+ days | Over 90 past due | DemandLetter or CollectionNotice |

## Dunning escalation ladder

Reminder1 → Reminder2 → Reminder3 → DemandLetter → CollectionNotice

## Collection status progression

None → Reminder1Sent → Reminder2Sent → Reminder3Sent → InCollections → SentToAgency
(exits at any point to: WrittenOff / PromiseToPay / PaymentPlan)

## Collection activity types

| Activity | Description |
|----------|-------------|
| DunningLetterSent | Automated or manual dunning letter |
| PhoneCall | Phone outreach to customer |
| Email | Email follow-up |
| InPersonVisit | On-site collection visit |
| PromiseToPay | Customer commitment to pay by date |
| PaymentPlanCreated | Installment arrangement |
| SentToCollections | Escalated to collections agency |
| WriteOffApproved | Balance written off |
| DisputeLogged | Customer disputes the charge |
| DisputeResolved | Dispute resolved |
| Note | General collection note |

## Credit memo reasons

| Reason | Use case |
|--------|----------|
| ReturnedGoods | Customer returned items |
| PricingError | Invoice was incorrect |
| Overpayment | Customer paid too much |
| Damaged | Goods arrived damaged |
| ServiceCredit | Service-level agreement credit |
| GoodwillAdjustment | Retention/satisfaction credit |
| Other | Anything else (document it) |

Credit memo statuses: Open → PartiallyApplied → FullyApplied (or Voided)

## Write-off reasons

Uncollectible · Bankruptcy · CustomerDispute · SmallBalance · AccountClosed · Deceased · Other

Write-offs require: approver authorization, Bad Debt Expense GL account, reason and approval date.

## Customer statement structure

Opening balance → all transactions (invoices, payments, credits) with running balance → closing balance → aging summary.
