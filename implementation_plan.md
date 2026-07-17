# InsightGreek CRM Finalization Plan

This plan addresses all requested changes to harden the app for production, ensure accurate claims, and add high-value features.

## Proposed Changes

### Documentation (README)
- **Model Truthfulness**: Revert the README model mentions from `DeBERTa-v3` back to `DistilBERT (distilbert-base-uncased)` to accurately reflect the training run and avoid overclaiming.
- **Deployment Info**: Add explicit, working deployment steps for a Split Architecture (Next.js on Vercel, Flask on Render).

### Backend Hardening (Flask API)
- **Input Validation**: Add explicit `request.is_json` and missing-field checking (`if not text:`) to `/api/submit-lead`, `/api/analyze-feedback`, and `/api/chat` to prevent malformed requests from crashing the server.
- **Explainable AI (XAI)**:
  - Add a lightweight rule-based/heuristic explainer in `predict_today.py` to generate a "why" behind lead scores (e.g., "Contains strong buying signals like 'budget'").
  - Add an `explanation` string column to the `Feedback` model in `app.py`.
  - Return this explanation in the API responses.
- **Analytics Endpoint**:
  - Add `GET /api/analytics` to aggregate lead volume and average sentiment grouped by date for the past 7-14 days.

### Frontend Enhancements (Next.js)
- **Model Explainability Display**: Update the Salesperson and Manager dashboards to display the new "Explanation" text alongside the confidence score.
- **Manager BI Dashboard**: 
  - Install `recharts` to render actual data visualizations (line charts for trends over time) instead of dummy data aggregations.
  - Wire the charts to consume data from `/api/analytics`.

### Testing & QA
- **RBAC Tests**: Create `backend/tests/test_auth.py` to write `pytest` suites proving that a Salesperson token cannot access Manager routes (`/api/users`) and that missing tokens are properly rejected with 401s.

## Open Questions

- **Database Migration**: Since we are using SQLite and SQLAlchemy (`db.create_all()`), adding the `explanation` column to the `Feedback` table will require dropping the table or manually altering it. Since this is a prototype, I plan to just drop and recreate the SQLite DB so the seed script populates it fresh with explanations. Is this acceptable?

## Verification Plan

### Automated Tests
- Run `pytest backend/tests/test_auth.py` to prove RBAC is secure.
- Verify 400 Bad Request responses on malformed inputs via `curl`.

### Manual Verification
- Log in as a Manager and view the newly implemented `recharts` trend graphs.
- Submit a Lead via Salesperson dashboard and verify the AI Explanation appears next to the score.
