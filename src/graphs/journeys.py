"""Map each accepted journey ID to the subgraphs it triggers."""

JOURNEY_SUBGRAPHS = {
    "subgraph_otp": ("subgraph_otp",),
    "subgraph_mpin": ("subgraph_mpin",),
    "subgraph_split_otp": ("subgraph_split_otp",),
    "subgraph_nb_password": ("subgraph_nb_password",),
}

RECOGNIZED_JOURNEY_IDS = frozenset(JOURNEY_SUBGRAPHS)
