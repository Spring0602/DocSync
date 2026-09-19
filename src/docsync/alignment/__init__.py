from docsync.models import Candidate, CandidateSet, CodeFact, DocumentClaim


def align(claims: list[DocumentClaim], facts: list[CodeFact], top_k: int = 5) -> list[CandidateSet]:
    result = []
    for claim in claims:
        matches = [
            fact
            for fact in facts
            if claim.subject
            and fact.property == claim.predicate
            and (fact.subject == claim.subject or fact.subject.endswith("." + claim.subject))
        ]
        exact = [fact for fact in matches if fact.subject == claim.subject]
        matches = sorted(exact or matches, key=lambda fact: fact.fact_id)
        if claim.source_hint:
            matches = [fact for fact in matches if fact.span.path == claim.source_hint]
        # Count ambiguity before truncation: top_k=1 cannot turn two matches into certainty.
        result.append(
            CandidateSet(
                claim_id=claim.claim_id,
                ambiguity=len(matches) > 1,
                reason="AMBIGUOUS"
                if len(matches) > 1
                else ("MATCH" if matches else "NO_CANDIDATE"),
                candidates=[
                    Candidate(
                        fact_id=f.fact_id,
                        rank=i + 1,
                        score=1.0,
                        features=["exact_symbol", "parameter_owner"]
                        + (["link_match"] if claim.source_hint else []),
                    )
                    for i, f in enumerate(matches[:top_k])
                ],
            )
        )
    return result
