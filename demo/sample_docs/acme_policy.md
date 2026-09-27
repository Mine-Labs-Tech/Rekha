# Acme Cloud Enterprise Customer Handbook & Service Policies

## 1. Subscription Plans & Pricing Terms
Acme Cloud provides three service tiers for global teams:
* **Starter Plan:** $49/month per team. Includes 5 seats, 100 GB storage, and community forum support.
* **Pro Plan:** $199/month per team. Includes 25 seats, 1 TB storage, and 8-hour email support response SLA.
* **Enterprise Plan:** $899/month per organization. Includes unlimited seats, custom dedicated compute nodes, and a guaranteed 99.99% uptime SLA.

All subscriptions are billed monthly or annually in advance via credit card or ACH bank transfer. We strictly do not accept cryptocurrency (Bitcoin, Ethereum) or cash payments under any circumstances.

## 2. Refund & Cancellation Policy
Customers are eligible for a 100% money-back refund within the first 30 days of their initial subscription if they are unsatisfied with the platform.
* Refund requests must be submitted through the account dashboard under Billing Settings.
* After 30 days from signup, all subscription charges are non-refundable. Prorated refunds are not issued for partial months.
* In the event of a documented system outage exceeding our 99.99% SLA commitment, Enterprise customers will receive service credits equal to 10% of their monthly invoice for each hour of downtime.

## 3. Data Privacy & Compliance Standards
Acme Cloud is SOC 2 Type II certified and complies with GDPR and HIPAA requirements.
* Customer data is encrypted in transit using TLS 1.3 and at rest using AES-256 encryption keys.
* Customer proprietary source code and documents are never used to train global public machine learning models.
* Accounts may request complete data deletion within 14 business days of account termination.

## 4. API Rate Limits & Technical Specifications
* Starter Plan: Maximum of 60 requests per minute per IP address.
* Pro Plan: Maximum of 300 requests per minute.
* Enterprise Plan: Up to 3,000 requests per minute with burst capability up to 5,000 requests per minute.
* HTTP 429 (Too Many Requests) is returned if rate limits are exceeded, with a `Retry-After` header indicating the required wait duration in seconds.
