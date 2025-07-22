# DataDeleteTool Development Roadmap

## Phase 1: Planning & Setup (1-2 weeks)
- **Initialize Project Structure** (High): Create folders (e.g., `src/`, `data/`, `docs/`), add `.gitignore` (ignore `.venv`, `*.db`), and set up `requirements.txt` (e.g., selenium, beautifulsoup4, sqlite3, click). Commit initial structure using Sublime Merge.
- **Configure Virtual Environment & IDE** (High): Set up Python 3.10+ venv in VS Code (select interpreter), install deps via `pip`. Add VS Code settings.json for Python linting/debugging.
- **Database Schema Design** (High): Define SQLite tables (e.g., users, addresses, broker_sites) as discussed. Implement basic CRUD functions in `db.py`.
- **Fetch & Cache IntelTechniques Workbook** (Medium): Write a script to scrape/cache the workbook site (https://inteltechniques.com/workbook.html) offline in JSON/SQLite.
- **Milestone**: Push setup to GitHub main branch. Test cross-OS by cloning on another machine.

## Phase 2: Core Development (2-4 weeks)
Focus: Build the essential scanning and storage functionality.
- **Menu-Driven Interface** (High): Use `click` or `typer` to create a CLI menu (like Metasploit) with options: scan brokers, store PII, view database. Debug in VS Code's terminal.
- **PII Input & Storage** (High): Automate user data entry (names, addresses, emails, etc.) into SQLite. Include state residency tracking for privacy laws (e.g., CCPA for California).
- **Basic Web Scraping for Brokers** (High): Integrate Selenium (with Firefox driver) to scan prelisted broker sites for PII. Flag matches and link to deletion pages.
- **Opt-Out Request Automation** (High): For found PII, auto-navigate to opt-out forms via Selenium, pre-fill where possible, and track requests in database (status: pending/resolved).
- **Offline/Online Hybrid Mode** (Medium): Query workbook for updates; fallback to cached list.
- **Milestone**: Functional core loop (input PII → scan → store results → generate requests). Commit features as branches (e.g., `feature/menu`) in Sublime Merge, merge to main.

## Phase 3: Advanced Features (3-5 weeks)
Focus: Enhance with social media integration and verification.
- **Social Media Scraping** (High): Add menu option to scrape sites (e.g., Twitter/X via API or Selenium) for PII in past posts. Maintain list of tied/untied accounts in database.
- **Verification & Tracking** (High): Periodically re-scan brokers/social sites to verify data removal; update database statuses. Add reminders for user-marked "resolved."
- **Privacy Law Integration** (Medium): Based on user state (from list: CA, VA, CO, etc.), customize requests (e.g., cite CCPA in forms).
- **Manual Verification Browser** (Medium): Launch Firefox via Selenium for user to visually confirm PII findings.
- **Export/Reporting** (Low): Generate XML/JSON reports of scanned data and requests.
- **Milestone**: Full end-to-end flow (scan brokers + social → automate requests → verify). Test on sample data, push updates to GitHub.

## Phase 4: Testing & Refinement (2-3 weeks)
Focus: Ensure reliability, security, and cross-OS compatibility.
- **Unit/Integration Tests** (High): Use pytest (add to requirements.txt) for scraping, DB ops, and menu functions. Run/debug in VS Code.
- **Cross-Platform Testing** (High): Test on macOS, Linux, Windows (e.g., Selenium drivers per OS). Fix any OS-specific issues (e.g., paths).
- **Security Audit** (Medium): Encrypt sensitive DB fields (e.g., via SQLCipher); add user consent prompts for scraping.
- **Error Handling & Logging** (Medium): Implement robust try/except for scraping failures; use logging module.
- **User Feedback Loop** (Low): Add menu for feature suggestions; refine based on iterations.
- **Milestone**: 80% test coverage; bug-free demo run. Create a release tag in Sublime Merge (e.g., v0.1).

## Phase 5: Deployment & Maintenance (Ongoing)
Focus: Package for users and handle updates.
- **Packaging** (Medium): Use PyInstaller for standalone executables (cross-OS binaries). Add setup script.
- **Documentation** (High): Expand README.md with usage guide, setup instructions, and disclaimer. Include in repo.
- **CI/CD Integration** (Low): Set up GitHub Actions for auto-tests on push (configure in `.github/workflows/` via VS Code).
- **Feature Iteration** (Ongoing): Monitor issues/pull requests on GitHub; add/remove based on user needs (e.g., more social sites).
- **Milestone**: Release v1.0 on GitHub; maintain via branches in Sublime Merge.
