We are creating a new web-app. It is a glorified AI chat agent.

Situation: financing company
Problem: when a contract is cancelled, any VAP/F&I products need to be checked for refund eligibility. There are thousands of different contract templates (PDF), which are difficult to locate and even more difficult to parse. For our initial phase, we just want to extract 3 data-points.

Partial Solution: we have a document repository that has OCR-ed/parsed all documents, generated embeddings, and stored them for retrieval. Documents are chunked by page (e.g. a 10 page document will have 10 rows in the DB).

Basic flow:
1. User searches for an account number (in the future, they can ask more complicated questions).
2. Our AI agent does some API calls/queries to find the contract ID
3. We check if the Contract ID has been retrieved previously. If so, return those values from our DB
4. If not, get the text/embeddings from that contract (already in our DB). Prompt to get our data elements
5. Present LLM output to user to validate. We need to show the PDF alongside the output. They can make corrections if needed and accept changes. Data is saved for auditability, and so we can retrieve it for future users

Basic UI requirements:
- Phase 1 will likely be 2-3 screens max. Prompt page, admin page (managing users), anything else?
- Desktop only. Will not be used on mobile.

Challenges:
- Contract terms can be state-specific

Technical Design:
- Deployment will be on AWS
- Frontend must be on next.js
- Backend should be Python for familiarity reasons
- Backend on ECS
- Frontend can be Fargate or ECS. My preference is ease of development.
- Auth will be handled by external provider (Auth0, Okta, etc)

Let's start with expanding these requirements. Consider any gaps in my description and requirements above. Are there any other critical decisions we need to think about this early on? Are there any features I should consider? This will feed into our initial requirement gathering and mockup design. We'll want to document our findings in `docs/product-docs`.