"""Demo fixture data - the ONLY file to touch when tailoring a pitch.

Everything the demo shows comes from here: customers, accounts, transactions,
FAQ entries, and the scenario cheat-sheets shown in the frontend picker.
Tweak names, balances, or merchants freely; no logic lives in this module.

Mutable state (card blocks, disputes, escalation counter) is in-memory only and
resets on restart - exactly what you want between pitch rehearsals.

A bank integrating for real would delete this file and point the routers at
their core-banking / card-management / CRM APIs instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from bankagent_shared.models import (
    Account,
    CardInfo,
    CustomerProfile,
    ScenarioInfo,
    Transaction,
)


@dataclass
class CustomerRecord:
    """A fixture customer: profile + credentials + transaction history."""

    profile: CustomerProfile
    account_number: str  # what the caller reads out to verify
    id_last4: str  # last 4 digits of SA ID / Botswana Omang
    transactions: list[Transaction] = field(default_factory=list)
    disputed_transaction_ids: set[str] = field(default_factory=set)
    # Where step-up approval codes go: the bank app on the registered device.
    # Masked description only - spoken by the agent, shown on dashboards.
    device_masked: str = "the Meridian app on your registered phone"


def _txn(
    txn_id: str,
    ts: str,
    merchant: str,
    description: str,
    amount: float,
    currency: str,
    status: str = "posted",
) -> Transaction:
    return Transaction(
        transaction_id=txn_id,
        ts=date.fromisoformat(ts),
        merchant=merchant,
        description=description,
        amount=amount,
        currency=currency,
        status=status,  # type: ignore[arg-type]
    )


# =============================================================================
# SCENARIO 1 - "happy path" balance & transactions demo
# Thabo Mokoena, Johannesburg. Cheque + savings, salary just landed, clean
# history. Use for: verify -> balance -> "did my salary come in?".
# =============================================================================
THABO = CustomerRecord(
    account_number="1002345678",
    id_last4="9087",
    profile=CustomerProfile(
        customer_id="cust-001",
        full_name="Thabo Mokoena",
        first_name="Thabo",
        accounts=[
            Account(
                account_id="acc-001-chq",
                account_masked="****5678",
                type="cheque",
                currency="ZAR",
                balance=18452.75,
            ),
            Account(
                account_id="acc-001-sav",
                account_masked="****5679",
                type="savings",
                currency="ZAR",
                balance=62010.00,
            ),
        ],
        card=CardInfo(last4="4821", status="active"),
    ),
    transactions=[
        _txn(
            "txn-001-010",
            "2026-07-03",
            "ACME Engineering",
            "SALARY - ACME ENGINEERING (PTY) LTD",
            28500.00,
            "ZAR",
        ),
        _txn(
            "txn-001-009", "2026-07-03", "Checkers Sixty60", "Groceries delivery", -1240.50, "ZAR"
        ),
        _txn("txn-001-008", "2026-07-02", "Sasol Garage Rosebank", "Fuel", -950.00, "ZAR"),
        _txn(
            "txn-001-007",
            "2026-07-01",
            "DSTV MultiChoice",
            "DSTV Premium subscription",
            -929.00,
            "ZAR",
        ),
        _txn("txn-001-006", "2026-06-30", "Vodacom", "Airtime & data", -499.00, "ZAR"),
        _txn("txn-001-005", "2026-06-28", "Woolworths Sandton", "Groceries", -876.30, "ZAR"),
        _txn("txn-001-004", "2026-06-27", "Netflix", "Subscription", -199.00, "ZAR"),
        _txn("txn-001-003", "2026-06-26", "Uber", "Trip - Sandton to Rosebank", -142.00, "ZAR"),
        _txn("txn-001-002", "2026-06-25", "City of Joburg", "Municipal rates", -1830.00, "ZAR"),
        _txn("txn-001-001", "2026-06-24", "Mr Price", "Clothing", -649.99, "ZAR"),
    ],
)

# =============================================================================
# SCENARIO 2 - flagged transaction / "was this me?" dispute demo
# Naledi Khumalo, Cape Town. Credit card with ONE FLAGGED transaction from an
# unfamiliar foreign online merchant. Use for: verify -> "anything unusual on
# my account?" -> dispute_transaction.
# =============================================================================
NALEDI = CustomerRecord(
    account_number="1007891234",
    id_last4="0842",
    profile=CustomerProfile(
        customer_id="cust-002",
        full_name="Naledi Khumalo",
        first_name="Naledi",
        accounts=[
            Account(
                account_id="acc-002-chq",
                account_masked="****1234",
                type="cheque",
                currency="ZAR",
                balance=9310.20,
            ),
            Account(
                account_id="acc-002-cc",
                account_masked="****1235",
                type="credit",
                currency="ZAR",
                balance=-12340.00,
                credit_limit=45000.00,
                available_credit=32660.00,
            ),
        ],
        card=CardInfo(last4="9034", status="active"),
        flags=["unusual_activity_review"],
    ),
    transactions=[
        # >>> The flagged one - the dispute demo pivots on this line. <<<
        _txn(
            "txn-002-010",
            "2026-07-04",
            "TECHGEAR ONLINE LU",
            "Online purchase - Luxembourg",
            -4899.00,
            "ZAR",
            status="flagged",
        ),
        _txn("txn-002-009", "2026-07-03", "Pick n Pay Gardens", "Groceries", -654.80, "ZAR"),
        _txn("txn-002-008", "2026-07-02", "Shell V&A Waterfront", "Fuel", -820.00, "ZAR"),
        _txn(
            "txn-002-007",
            "2026-07-01",
            "Discovery Health",
            "Medical aid contribution",
            -3450.00,
            "ZAR",
        ),
        _txn("txn-002-006", "2026-06-29", "Spotify", "Subscription", -64.99, "ZAR"),
        _txn("txn-002-005", "2026-06-28", "Clicks Sea Point", "Pharmacy", -312.45, "ZAR"),
        _txn("txn-002-004", "2026-06-27", "Takealot", "Online order", -1499.00, "ZAR"),
        _txn("txn-002-003", "2026-06-26", "Kauai Kloof Street", "Lunch", -145.00, "ZAR"),
        _txn("txn-002-002", "2026-06-25", "MyCiTi", "Bus fare top-up", -200.00, "ZAR"),
    ],
)

# =============================================================================
# SCENARIO 3 - sensitive conversation: near credit limit
# Kagiso Tau, Gaborone. Credit card at ~94% of limit; a declined attempt is in
# the history as "pending". Use for: verify -> "why was my card declined?" ->
# agent explains available credit tactfully, offers FAQ or human.
# =============================================================================
KAGISO = CustomerRecord(
    account_number="1004567890",
    id_last4="3319",
    profile=CustomerProfile(
        customer_id="cust-003",
        full_name="Kagiso Tau",
        first_name="Kagiso",
        accounts=[
            Account(
                account_id="acc-003-chq",
                account_masked="****7890",
                type="cheque",
                currency="BWP",
                balance=1180.55,
            ),
            Account(
                account_id="acc-003-cc",
                account_masked="****7891",
                type="credit",
                currency="BWP",
                balance=-18750.00,
                credit_limit=20000.00,
                available_credit=1250.00,
            ),
        ],
        card=CardInfo(last4="6617", status="active"),
    ),
    transactions=[
        _txn(
            "txn-003-010",
            "2026-07-05",
            "Game City Gaborone",
            "POS attempt - declined (insufficient credit)",
            -2100.00,
            "BWP",
            status="pending",
        ),
        _txn("txn-003-009", "2026-07-04", "Choppies Hyper", "Groceries", -845.60, "BWP"),
        _txn("txn-003-008", "2026-07-02", "Engen Riverwalk", "Fuel", -610.00, "BWP"),
        _txn("txn-003-007", "2026-07-01", "Orange Botswana", "Mobile contract", -399.00, "BWP"),
        _txn("txn-003-006", "2026-06-30", "Airlink", "Flight GBE-JNB", -3200.00, "BWP"),
        _txn(
            "txn-003-005", "2026-06-28", "Cresta Lodge Gaborone", "Accommodation", -1850.00, "BWP"
        ),
        _txn("txn-003-004", "2026-06-27", "Woolworths Riverwalk", "Clothing", -720.00, "BWP"),
        _txn("txn-003-003", "2026-06-26", "Spar Kgale View", "Groceries", -430.25, "BWP"),
        _txn("txn-003-002", "2026-06-24", "BPC", "Electricity prepaid", -500.00, "BWP"),
    ],
)

# =============================================================================
# SCENARIO 4 - action demo: report a lost card
# Amogelang Seretse, Francistown. Card is ACTIVE and gets blocked live during
# the demo (state mutates in memory; restart the backend to reset).
# Use for: verify -> report_card_lost -> confirmation + replacement ETA.
# =============================================================================
AMOGELANG = CustomerRecord(
    account_number="1009876543",
    id_last4="7754",
    profile=CustomerProfile(
        customer_id="cust-004",
        full_name="Amogelang Seretse",
        first_name="Amogelang",
        accounts=[
            Account(
                account_id="acc-004-chq",
                account_masked="****6543",
                type="cheque",
                currency="BWP",
                balance=9320.40,
            ),
            Account(
                account_id="acc-004-sav",
                account_masked="****6544",
                type="savings",
                currency="BWP",
                balance=27500.00,
            ),
        ],
        card=CardInfo(last4="7742", status="active"),
    ),
    transactions=[
        _txn("txn-004-008", "2026-07-04", "Shoprite Francistown", "Groceries", -560.90, "BWP"),
        _txn("txn-004-007", "2026-07-03", "Mascom", "Airtime", -150.00, "BWP"),
        _txn("txn-004-006", "2026-07-01", "Botswana Life", "Policy premium", -890.00, "BWP"),
        _txn("txn-004-005", "2026-06-30", "Nando's Galo Mall", "Dining", -215.00, "BWP"),
        _txn("txn-004-004", "2026-06-28", "Sefalana Cash & Carry", "Household", -1120.75, "BWP"),
        _txn("txn-004-003", "2026-06-27", "Puma Energy", "Fuel", -540.00, "BWP"),
        _txn("txn-004-002", "2026-06-25", "CNA Francistown", "Stationery", -186.50, "BWP"),
        _txn("txn-004-001", "2026-06-23", "Employer - Debswana", "SALARY", 14200.00, "BWP"),
    ],
)

# =============================================================================
# SCENARIO 5 - guardrails & escalation demo
# Sipho Dlamini, Durban. Healthy savings; the SCRIPT (not the data) drives this
# one: ask for investment advice (agent declines), ask to transfer money
# (agent declines - needs stronger auth), then ask for a human (escalation
# with summary carried forward).
# =============================================================================
SIPHO = CustomerRecord(
    account_number="1003216549",
    id_last4="5561",
    profile=CustomerProfile(
        customer_id="cust-005",
        full_name="Sipho Dlamini",
        first_name="Sipho",
        accounts=[
            Account(
                account_id="acc-005-sav",
                account_masked="****6549",
                type="savings",
                currency="ZAR",
                balance=150320.11,
            ),
            Account(
                account_id="acc-005-chq",
                account_masked="****6550",
                type="cheque",
                currency="ZAR",
                balance=7204.88,
            ),
        ],
        card=CardInfo(last4="2296", status="active"),
    ),
    transactions=[
        _txn(
            "txn-005-007", "2026-07-02", "Interest", "Savings interest capitalised", 812.40, "ZAR"
        ),
        _txn("txn-005-006", "2026-07-01", "Debit order", "Transfer to savings", 5000.00, "ZAR"),
        _txn("txn-005-005", "2026-06-30", "Spar Musgrave", "Groceries", -734.20, "ZAR"),
        _txn("txn-005-004", "2026-06-28", "Engen Berea", "Fuel", -880.00, "ZAR"),
        _txn("txn-005-003", "2026-06-27", "Old Mutual", "Unit trust debit order", -2500.00, "ZAR"),
        _txn("txn-005-002", "2026-06-26", "Gateway Cinema", "Entertainment", -240.00, "ZAR"),
        _txn("txn-005-001", "2026-06-24", "eThekwini Municipality", "Utilities", -1610.00, "ZAR"),
    ],
)

# -----------------------------------------------------------------------------
# Lookup tables used by the routers.
# -----------------------------------------------------------------------------
CUSTOMERS: dict[str, CustomerRecord] = {
    rec.profile.customer_id: rec for rec in (THABO, NALEDI, KAGISO, AMOGELANG, SIPHO)
}
BY_ACCOUNT_NUMBER: dict[str, CustomerRecord] = {
    rec.account_number: rec for rec in CUSTOMERS.values()
}

# -----------------------------------------------------------------------------
# FAQ entries served by GET /api/v1/faq/search (keyword-scored).
# General banking questions that need NO account access.
# -----------------------------------------------------------------------------
FAQS: list[dict[str, str]] = [
    {
        "question": "What are your branch operating hours?",
        "answer": "Branches are open weekdays 08:30-16:00 and Saturdays 08:30-12:00. "
        "Selected mall branches stay open until 17:00 on weekdays.",
    },
    {
        "question": "How do I reset my banking app PIN?",
        "answer": "Open the app, choose 'Forgot PIN' on the login screen, and follow the "
        "prompts. You will need your ID number and registered phone nearby.",
    },
    {
        "question": "What fees apply to an immediate payment?",
        "answer": "Immediate (real-time) payments cost R10 / P10 per transaction "
        "regardless of amount. Standard EFTs are free on digital channels.",
    },
    {
        "question": "How long does a new card take to arrive?",
        "answer": "Replacement cards are delivered to your chosen branch within 5 working "
        "days. Courier delivery to your address is available in main centres.",
    },
    {
        "question": "What is the daily ATM withdrawal limit?",
        "answer": "The default daily ATM limit is R5,000 / P5,000. You can adjust it in "
        "the app under Card Settings, up to R20,000 / P20,000.",
    },
    {
        "question": "How do I open a savings account?",
        "answer": "You can open a savings account in the app in about five minutes with "
        "your ID number. No minimum balance is required.",
    },
    {
        "question": "Are my deposits insured?",
        "answer": "Deposits are covered by the applicable national deposit insurance "
        "scheme up to the regulated limit per depositor.",
    },
    {
        "question": "How do I send money to another bank?",
        "answer": "Use Payments in the app, add the beneficiary's account and branch "
        "code, and choose standard EFT (1-2 business days) or immediate payment.",
    },
    {
        "question": "What exchange rate applies to card purchases abroad?",
        "answer": "International card purchases use the network rate on settlement day "
        "plus a 2% currency conversion fee.",
    },
    {
        "question": "How do I update my contact details?",
        "answer": "For security, contact detail changes require the app with biometric "
        "confirmation, or a branch visit with your ID document.",
    },
]

# -----------------------------------------------------------------------------
# Scenario cheat-sheets for the demo frontend picker. `id` doubles as the room
# name prefix (demo-<id>-xxxxxx) so transcripts can be correlated to scenarios.
# -----------------------------------------------------------------------------
SCENARIOS: list[ScenarioInfo] = [
    ScenarioInfo(
        id="thabo",
        title="Happy path - balance & salary",
        customer_name=THABO.profile.full_name,
        account_number=THABO.account_number,
        id_last4=THABO.id_last4,
        description="Clean account. Straightforward verify, balance and transaction queries.",
        suggested_lines=[
            "Hi, I'd like to check my balance please.",
            "Has my salary come in yet?",
            "What did I spend at Checkers?",
        ],
    ),
    ScenarioInfo(
        id="naledi",
        title="Flagged transaction - dispute",
        customer_name=NALEDI.profile.full_name,
        account_number=NALEDI.account_number,
        id_last4=NALEDI.id_last4,
        description="One flagged foreign online purchase. Shows grounded fraud handling and an action tool.",
        suggested_lines=[
            "Is there anything unusual on my account?",
            "I don't recognise that Luxembourg payment.",
            "Please dispute it - I never made that purchase.",
        ],
    ),
    ScenarioInfo(
        id="kagiso",
        title="Card declined - near credit limit",
        customer_name=KAGISO.profile.full_name,
        account_number=KAGISO.account_number,
        id_last4=KAGISO.id_last4,
        description="Credit card at 94% of limit. A sensitive conversation handled tactfully.",
        suggested_lines=[
            "My card was declined at Game City yesterday - why?",
            "How much credit do I have left?",
        ],
    ),
    ScenarioInfo(
        id="amogelang",
        title="Lost card - block & replace",
        customer_name=AMOGELANG.profile.full_name,
        account_number=AMOGELANG.account_number,
        id_last4=AMOGELANG.id_last4,
        description="The action demo: card gets blocked live, with a reference number and replacement ETA.",
        suggested_lines=[
            "I've lost my card, please block it.",
            "When will the replacement arrive?",
        ],
    ),
    ScenarioInfo(
        id="sipho",
        title="Out of scope - refusal & human handoff",
        customer_name=SIPHO.profile.full_name,
        account_number=SIPHO.account_number,
        id_last4=SIPHO.id_last4,
        description="Guardrails demo: declines investment advice and transfers, then escalates with a summary.",
        suggested_lines=[
            "Should I move my savings into shares?",
            "Transfer R50,000 to my brother please.",
            "Fine, let me talk to a real person.",
        ],
    ),
]

# -----------------------------------------------------------------------------
# Mutable in-memory state (resets on restart).
# -----------------------------------------------------------------------------
_escalation_counter = 0


def next_escalation_ref(today: str) -> str:
    """ESC-YYYYMMDD-NNN, e.g. ESC-20260706-001."""
    global _escalation_counter
    _escalation_counter += 1
    return f"ESC-{today}-{_escalation_counter:03d}"


def reset_state() -> None:
    """Restore all mutable fixture state. Used by tests."""
    global _escalation_counter
    _escalation_counter = 0
    for rec in CUSTOMERS.values():
        rec.disputed_transaction_ids.clear()
        if rec.profile.card is not None:
            rec.profile.card.status = "active"
