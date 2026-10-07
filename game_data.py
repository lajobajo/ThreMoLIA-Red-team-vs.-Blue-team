"""Game content: DFD nodes, attacks, mitigations and the rules that compare them.

Node ids match the section ids in templates/dfd.html.
"""

ATTACKS_PER_GAME = 3
BLUE_WINS_IF_BLOCKED_AT_LEAST = 2

NODES = {
    "doctor": "Doctor (external)",
    "patient": "Patient",
    "web": "Web Frontend",
    "chatbot": "AI Chatbot",
    "ai-database": "AI Database",
    "backend": "Backend API",
    "bookings": "Bookings Database",
    "clinical": "Clinical Database",
    "analysis": "AI Analysis",
    "staff-doctor": "Doctor (staff)",
    "management": "Management Staff",
}

# Attacks Red can pick. "targets" are the nodes the attack can be aimed at.
ATTACKS = {
    "sql_injection": {
        "name": "SQL Injection",
        "stride": "Tampering",
        "targets": ["backend", "bookings", "clinical", "ai-database"],
    },
    "xss": {
        "name": "Cross-Site Scripting (XSS)",
        "stride": "Tampering",
        "targets": ["web"],
    },
    "prompt_injection": {
        "name": "Prompt Injection",
        "stride": "Tampering",
        "targets": ["chatbot"],
    },
    "credential_stuffing": {
        "name": "Credential Stuffing",
        "stride": "Spoofing",
        "targets": ["web", "staff-doctor", "management"],
    },
    "dos": {
        "name": "Denial of Service",
        "stride": "Denial of Service",
        "targets": ["web", "chatbot", "backend"],
    },
    "data_exfiltration": {
        "name": "Data Exfiltration",
        "stride": "Information Disclosure",
        "targets": ["bookings", "clinical", "ai-database"],
    },
    "privilege_escalation": {
        "name": "Privilege Escalation",
        "stride": "Elevation of Privilege",
        "targets": ["backend", "analysis"],
    },
    "model_poisoning": {
        "name": "Model Poisoning",
        "stride": "Tampering",
        "targets": ["analysis", "ai-database"],
    },
    "log_tampering": {
        "name": "Log Tampering",
        "stride": "Repudiation",
        "targets": ["backend", "clinical"],
    },
}

# Mitigations Blue can buy. "blocks" are attack ids the mitigation stops and
# "targets" are the nodes it can be placed on. The more attacks a mitigation
# blocks, the more it costs.
MITIGATIONS = {
    "input_validation": {
        "name": "Input Validation / Parameterized Queries",
        "cost": 4,
        "blocks": ["sql_injection", "xss", "prompt_injection"],
        "targets": [
            "backend", "bookings", "clinical", "ai-database", "web", "chatbot",
        ],
    },
    "rate_limiting": {
        "name": "Rate Limiting / WAF",
        "cost": 3,
        "blocks": ["dos", "credential_stuffing"],
        "targets": ["web", "chatbot", "backend"],
    },
    "rbac": {
        "name": "RBAC / Least Privilege",
        "cost": 3,
        "blocks": ["privilege_escalation", "data_exfiltration"],
        "targets": ["backend", "bookings", "clinical", "ai-database", "analysis"],
    },
    "mfa": {
        "name": "Multi-Factor Authentication",
        "cost": 2,
        "blocks": ["credential_stuffing"],
        "targets": ["web", "staff-doctor", "management"],
    },
    "encryption_at_rest": {
        "name": "Encryption at Rest",
        "cost": 2,
        "blocks": ["data_exfiltration"],
        "targets": ["bookings", "clinical", "ai-database"],
    },
    "prompt_guardrails": {
        "name": "Prompt Guardrails",
        "cost": 2,
        "blocks": ["prompt_injection"],
        "targets": ["chatbot"],
    },
    "training_data_integrity": {
        "name": "Training Data Integrity Checks",
        "cost": 2,
        "blocks": ["model_poisoning"],
        "targets": ["analysis", "ai-database"],
    },
    "audit_logging": {
        "name": "Tamper-Proof Audit Logging",
        "cost": 1,
        "blocks": ["log_tampering"],
        "targets": ["backend", "clinical"],
    },
}


def validate_red_attacks(picks):
    """Return an error message, or None if Red's picks are valid."""
    if len(picks) != ATTACKS_PER_GAME:
        return f"Pick exactly {ATTACKS_PER_GAME} attacks."

    seen = set()
    for pick in picks:
        attack = ATTACKS.get(pick["attack"])
        if attack is None or pick["target"] not in attack["targets"]:
            return "Every attack needs a valid target."

        key = (pick["attack"], pick["target"])
        if key in seen:
            return "You can't pick the same attack on the same target twice."
        seen.add(key)

    return None


def validate_blue_mitigations(picks, budget):
    """Return an error message, or None if Blue's picks are valid."""
    if not picks:
        return "Pick at least one mitigation."

    seen = set()
    total = 0
    for pick in picks:
        mitigation = MITIGATIONS.get(pick["mitigation"])
        if mitigation is None or pick["node"] not in mitigation["targets"]:
            return "Every mitigation needs a valid node."

        key = (pick["mitigation"], pick["node"])
        if key in seen:
            return "You can't place the same mitigation on the same node twice."
        seen.add(key)

        total += mitigation["cost"]

    if total > budget:
        return f"Over budget: {total} / {budget}."

    return None


def resolve(red_attacks, blue_mitigations):
    """Compare Red's attacks with Blue's mitigations and decide the winner."""
    attack_results = []
    mitigation_results = [
        {
            "name": MITIGATIONS[m["mitigation"]]["name"],
            "node": NODES[m["node"]],
            "cost": MITIGATIONS[m["mitigation"]]["cost"],
            "stopped": [],
        }
        for m in blue_mitigations
    ]

    for pick in red_attacks:
        blocked_by = []
        for i, m in enumerate(blue_mitigations):
            mitigation = MITIGATIONS[m["mitigation"]]
            if m["node"] == pick["target"] and pick["attack"] in mitigation["blocks"]:
                blocked_by.append(mitigation["name"])
                mitigation_results[i]["stopped"].append(
                    ATTACKS[pick["attack"]]["name"]
                )

        attack_results.append({
            "name": ATTACKS[pick["attack"]]["name"],
            "stride": ATTACKS[pick["attack"]]["stride"],
            "target": NODES[pick["target"]],
            "blocked": bool(blocked_by),
            "blocked_by": blocked_by,
        })

    blocked_count = sum(1 for r in attack_results if r["blocked"])

    return {
        "attacks": attack_results,
        "mitigations": mitigation_results,
        "blocked": blocked_count,
        "succeeded": len(attack_results) - blocked_count,
        "winner": (
            "blue" if blocked_count >= BLUE_WINS_IF_BLOCKED_AT_LEAST else "red"
        ),
    }
