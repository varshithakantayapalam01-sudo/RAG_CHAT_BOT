# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview

The objective of this project is to build a **facts-only FAQ assistant** for mutual fund schemes, using **Groww** as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources, such as AMC (Asset Management Company) websites, AMFI, and SEBI.

The system must **strictly avoid** providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

---

## Objective

Design and implement a lightweight **Retrieval-Augmented Generation (RAG)**-based assistant that:

- Answers factual queries about mutual fund schemes
- Uses a curated corpus of official documents
- Provides concise, source-backed responses

---

## Target Users

- Retail investors comparing mutual fund schemes
- Customer support and content teams handling repetitive mutual fund queries

---

## Scope of Work

### 1. Corpus Definition

- **Selected AMC:** HDFC Asset Management Company (HDFC AMC)
- **Selected Schemes (5):**

| # | Scheme Name | Category | Groww URL |
|---|---|---|---|
| 1 | HDFC Mid-Cap Fund – Direct Growth | Mid-Cap | [Link](https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth) |
| 2 | HDFC Equity Fund – Direct Growth | Multi-Cap / Flexi-Cap | [Link](https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth) |
| 3 | HDFC Focused Fund – Direct Growth | Focused / Flexi-Cap | [Link](https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth) |
| 4 | HDFC ELSS Tax Saver Fund – Direct Plan Growth | ELSS (Tax Saving) | [Link](https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth) |
| 5 | HDFC Large Cap Fund – Direct Growth | Large-Cap | [Link](https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth) |

- **Corpus sources to collect (15–25 official public URLs):**
  - Scheme factsheets
  - KIM (Key Information Memorandum)
  - SID (Scheme Information Document)
  - AMC FAQ/help pages
  - AMFI/SEBI guidance pages
  - Statement and tax document download guides

### 2. FAQ Assistant Requirements

The assistant must answer **facts-only queries**, such as:

| Query Type | Example |
|---|---|
| Expense ratio | Expense ratio of a scheme |
| Exit load | Exit load details |
| Minimum SIP | Minimum SIP amount |
| Lock-in period | ELSS lock-in period |
| Risk classification | Riskometer classification |
| Benchmark | Benchmark index |
| Processes | How to download statements or capital gains reports |

**Response constraints:**

- Each response is limited to a **maximum of 3 sentences**
- Each response includes **exactly one citation link**
- Each response includes a footer: `"Last updated from sources: <date>"`

### 3. Refusal Handling

The assistant must **refuse** non-factual or advisory queries, such as:

> *"Should I invest in this fund?"*
> *"Which fund is better?"*

Refusal responses should:

- Be polite and clearly worded
- Reinforce the facts-only limitation
- Provide a relevant educational link (e.g., AMFI or SEBI resource)

### 4. User Interface (Minimal)

The solution should include a simple interface with:

- A **welcome message**
- **Three example questions**
- A visible disclaimer: **"Facts-only. No investment advice."**

---

## Constraints

### Data and Sources

- Use **only** official public sources (AMC, AMFI, SEBI)
- Do **not** use third-party blogs or aggregator websites

### Privacy and Security

> [!CAUTION]
> The system must **never** collect, store, or process:
> - PAN or Aadhaar numbers
> - Account numbers
> - OTPs
> - Email addresses or phone numbers

### Content Restrictions

- No investment advice or recommendations
- No performance comparisons or return calculations
- For performance-related queries, provide a link to the official factsheet only

### Transparency

- Responses must be short, factual, and verifiable
- Every answer must include a source link and last updated date

---

## Expected Deliverables

### 1. README Document

- Setup instructions
- Selected AMC and schemes
- Architecture overview (RAG approach)
- Known limitations

### 2. Disclaimer Snippet

> "Facts-only. No investment advice."

---

## Success Criteria

| Criteria | Description |
|---|---|
| ✅ Accuracy | Accurate retrieval of factual mutual fund information |
| ✅ Facts-only | Strict adherence to facts-only responses |
| ✅ Citations | Consistent inclusion of valid source citations |
| ✅ Refusal handling | Proper refusal of advisory queries |
| ✅ UI/UX | Clean, minimal, and user-friendly interface |

---

## Summary

> The goal is to build a **trustworthy, transparent, and compliant** mutual fund FAQ assistant that prioritizes **accuracy over intelligence**. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
