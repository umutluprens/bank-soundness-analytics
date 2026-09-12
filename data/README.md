# Data schema

The original licensed dataset is not included. Place an authorised CSV file in `data/raw/` and pass its path to `run_analysis.py`.

The loader accepts common variations in spacing and capitalisation and converts them to snake case. Expected columns are:

| Field | Description |
| --- | --- |
| `bank_name` | Financial institution name |
| `year` | Reporting year |
| `country` | Country of operation |
| `total_capital_ratio` | Total regulatory capital ratio; used only to define the proxy target |
| `tier1_ratio` | Tier 1 capital ratio |
| `texas_ratio` | Credit-problem exposure relative to tangible capital/reserves |
| `problem_loans_ratio` | Problem or non-performing loans ratio |
| `loan_loss_reserve_to_problem_loans` | Coverage of problem loans |
| `net_interest_margin` | Net interest margin |
| `roaa` | Return on average assets |
| `roae` | Return on average equity |
| `liquid_assets_total_deposits_borrowings` | Liquidity measure |
| `total_debt_total_equity` | Leverage measure |
| `liquidity_coverage_ratio` | Liquidity coverage ratio |
| `book_value_per_share_growth` | Book-value growth |
| `operating_return_on_assets` | Operating return on assets |
| `non_operating_expense_ratio` | Non-operating expense ratio |
| `bicra` | Banking Industry Country Risk Assessment group |
| `bank_type` | Bank business-model category |

Do not commit licensed exports, annual-report PDFs, credentials, or API keys.

