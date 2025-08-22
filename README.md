# Tech Jobs & Internships Notification Service

**Receive instant filtered job alerts for students and new grads.**

Get notified by **email** or **SMS** about the newest postings in the most popular open-source tech job boards:

- [SimplifyJobs/New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions)
- [SimplifyJobs/Summer2026-Internships](https://github.com/SimplifyJobs/Summer2026-Internships)

This project polls these repositories frequently, detects new job listings, and sends you **filtered notifications** that **match your preferences**.

## Key Features

- **Real-time-ish updates:** Polls the repos every 15 minutes by default, so you're among the first to hear about new listings.
- **Custom keyword filtering:** Configure preferences by keywords (tech stack, role, or location). You’ll only get notifications for listings that match what you care about. Or receive all of them!
- **Flexible channels:** Receive alerts via **email**, **SMS**, or both.
- **Self-service preferences:** Edit your filter and notification preferences or unsubscribe anytime through simple links delivered directly to your inbox/phone.
- **Secure & compliant:** Includes 30-day unsubscribe links and short-lived verification/edit tokens.

## Architecture

- **Backend (FastAPI)**
  - Polls the Simplify GitHub repos.
  - Parses diffs into structured job listings.
  - Stores user preferences in a SQLite database.
  - Sends notifications via Resend and Twilio.
- **Frontend (React + Vite + Tailwind + shadcn/ui)**
  - Simple UI for subscription and preference management.
  - Connects to the FastAPI backend via REST API.

## How It Works

1. **Subscribe**
    - Provide your email/phone and notification preferences via the frontend.
    - You’ll get a verification link to confirm.

2. **Filter**
    - Enter keywords like `"backend"`, `"San Francisco"`, `"Python"` — only matching postings from the repos trigger notifications.

3. **Notify**
    - When new listings hit the repo, the system matches them against your filters and sends you an instant email/SMS.

4. **Edit/Unsubscribe**
    - Links in every message let you edit preferences or unsubscribe.

## Contributing

Contributions are welcome!
- Fork the repo
- Create a feature branch
- Submit a PR

