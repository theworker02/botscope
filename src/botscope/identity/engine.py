"""Identity verification — UA claims alone never establish verified identity."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from botscope.identity.ranges import PublishedRangeIndex
from botscope.normalize.event import NormalizedEvent
from botscope.signatures.store import Signature, SignatureStore


class IdentityStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED_CLAIM = "UNVERIFIED CLAIM"
    MISMATCH = "MISMATCH"
    NO_CLAIM = "NO CLAIM"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT EVIDENCE"


@dataclass(frozen=True)
class IdentityResult:
    claimed_name: str | None
    status: IdentityStatus
    confidence: float
    evidence: list[str] = field(default_factory=list)
    signature: Signature | None = None
    extras: dict[str, Any] = field(default_factory=dict)


_OPERATOR_ALIASES: dict[str, set[str]] = {
    "googlebot": {"google"},
    "bingbot": {"microsoft", "bing"},
    "adidxbot": {"microsoft", "bing"},
    "gptbot": {"openai"},
    "claudebot": {"anthropic"},
}


class IdentityEngine:
    """Determine whether claimed bot identity is consistent with available signals."""

    def __init__(
        self,
        signatures: SignatureStore | None = None,
        range_index: PublishedRangeIndex | None = None,
    ) -> None:
        self.signatures = signatures or SignatureStore.load_bundled()
        self.range_index = range_index or PublishedRangeIndex()

    def verify(self, event: NormalizedEvent) -> IdentityResult:
        ua = event.user_agent or ""
        claim = self.signatures.match_user_agent(ua)
        if claim is None:
            return IdentityResult(
                claimed_name=None,
                status=IdentityStatus.NO_CLAIM,
                confidence=0.0,
                evidence=["No known bot identity claimed in User-Agent"],
            )

        evidence: list[str] = [f"User-Agent claims: {claim.name}"]
        checks_passed = 0
        checks_failed = 0
        checks_total = 0

        # Reverse DNS consistency (when available)
        if claim.rdns_suffixes:
            checks_total += 1
            rdns = (event.reverse_dns or "").lower().rstrip(".")
            if not rdns:
                evidence.append("Reverse DNS unavailable — cannot confirm claim")
            elif any(rdns.endswith(suffix.lower()) for suffix in claim.rdns_suffixes):
                checks_passed += 1
                evidence.append(f"Reverse DNS consistent with {claim.name}: {rdns}")
            else:
                checks_failed += 1
                evidence.append(
                    f"Reverse DNS mismatch for {claim.name}: {rdns or '(empty)'}"
                )

        # ASN / network owner consistency (when available)
        if claim.expected_asns:
            checks_total += 1
            if event.asn is None:
                evidence.append("ASN unavailable — cannot confirm claim")
            elif event.asn in claim.expected_asns:
                checks_passed += 1
                evidence.append(f"ASN {event.asn} matches published expectation")
            else:
                checks_failed += 1
                evidence.append(f"ASN {event.asn} does not match published expectation")

        if claim.network_owner_tokens:
            checks_total += 1
            owner = (event.network_owner or "").lower()
            if not owner:
                evidence.append("Network owner unavailable — cannot confirm claim")
            elif any(tok.lower() in owner for tok in claim.network_owner_tokens):
                checks_passed += 1
                evidence.append(f"Network owner consistent: {event.network_owner}")
            else:
                checks_failed += 1
                evidence.append(
                    f"Network owner unrelated to {claim.name}: {event.network_owner}"
                )

        # Published CIDR membership (signature ranges + live range index)
        if event.src_address and (claim.network_ranges or len(self.range_index) > 0):
            checks_total += 1
            in_sig_range = self._ip_in_signature_ranges(event.src_address, claim)
            operators = self.range_index.operators_for_ip(event.src_address)
            expected_ops = self._expected_operators(claim)
            in_index = bool(expected_ops.intersection(operators))
            if in_sig_range or in_index:
                checks_passed += 1
                detail = "signature CIDR" if in_sig_range else f"published ranges ({', '.join(sorted(operators))})"
                evidence.append(f"Source IP in published crawler ranges ({detail})")
            elif operators and not expected_ops.intersection(operators):
                checks_failed += 1
                evidence.append(
                    f"Source IP matches unrelated published ranges: {', '.join(sorted(operators))}"
                )
            else:
                evidence.append("Source IP not found in loaded published crawler ranges")

        # Forward-confirmed reverse DNS (when both present)
        if event.reverse_dns and event.forward_dns and event.src_address:
            checks_total += 1
            if event.forward_dns == event.src_address:
                checks_passed += 1
                evidence.append("Forward-confirmed reverse DNS succeeded")
            else:
                checks_failed += 1
                evidence.append("Forward-confirmed reverse DNS failed")

        if checks_failed > 0 and checks_passed == 0:
            return IdentityResult(
                claimed_name=claim.name,
                status=IdentityStatus.MISMATCH,
                confidence=0.2,
                evidence=[*evidence, "Result: UNVERIFIED CLAIM / MISMATCH — do not treat as verified"],
                signature=claim,
            )

        if checks_total == 0 or (checks_passed == 0 and checks_failed == 0):
            return IdentityResult(
                claimed_name=claim.name,
                status=IdentityStatus.UNVERIFIED_CLAIM,
                confidence=0.35,
                evidence=[*evidence, "User-Agent alone does not establish verified identity", "Result: UNVERIFIED CLAIM"],
                signature=claim,
            )

        if checks_passed > 0 and checks_failed == 0:
            return IdentityResult(
                claimed_name=claim.name,
                status=IdentityStatus.VERIFIED,
                confidence=min(0.95, 0.6 + 0.1 * checks_passed),
                evidence=[*evidence, "Result: VERIFIED with corroborating signals"],
                signature=claim,
            )

        return IdentityResult(
            claimed_name=claim.name,
            status=IdentityStatus.INSUFFICIENT_EVIDENCE,
            confidence=0.4,
            evidence=[*evidence, "Mixed signals — insufficient for verification"],
            signature=claim,
        )

    @staticmethod
    def _expected_operators(claim: Signature) -> set[str]:
        name = claim.name.lower()
        ops: set[str] = set()
        for key, aliases in _OPERATOR_ALIASES.items():
            if key in name:
                ops |= aliases
        for tok in claim.network_owner_tokens:
            ops.add(tok.lower())
        return ops

    @staticmethod
    def _ip_in_signature_ranges(address: str, claim: Signature) -> bool:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        for cidr in claim.network_ranges:
            try:
                if ip in ipaddress.ip_network(cidr, strict=False):
                    return True
            except ValueError:
                continue
        return False
