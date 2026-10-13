"""Subgraphs selected by the incoming journey ID."""

RECOGNIZED_JOURNEY_IDS = frozenset(
    {
        "subgraph_otp",
        "subgraph_mpin",
        "subgraph_split_otp",
        "subgraph_nb_password",
    }
)
