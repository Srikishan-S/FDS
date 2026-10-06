# SEEF — Self-Evolving Feature Engineering Framework

## Algorithm pseudocode

```text
TRAIN one classifier on an independent stable training set
FREEZE classifier weights
INITIALIZE stream, detector ensemble, episodic memory, controller,
           genealogy, active representation and feature version registry
FOR each observation x_t:
    p_production = classifier(active_representation(x_t))
    p_static = original_classifier(x_t)
    FOR each shadow candidate:
        record p_candidate before observing the label
    queue predictions and observation
    WHEN the delayed label becomes available:
        update error detectors and labelled evaluation window
    WHEN a labelled window is complete:
        calculate real accuracy, precision, recall, F1, AUC, latency
        create structured fingerprint relative to reference window
        scale fixed fingerprint coordinates, then normalize
        combine error, distribution, correlation, confidence,
                residual and detector-vote signals
        IF two windows confirm drift and no active arena:
            retrieve top-K successful episodes using cosine similarity
            choose contextual epsilon-greedy action
            generate bounded context-relevant candidate catalog
            fit unsupervised transform parameters on past window
            rank candidates using relevance, information, history,
                 redundancy and complexity
            start shortlisted prospective shadow configurations
        IF a complete future shadow window is available:
            calculate paired F1, latency, stability and confidence
            track consecutive passes for every safety criterion
            require two extra qualification windows if not recalled
            IF any candidate passes:
                select best passing gain
                deploy a new representation version
                update strategy reward from measured outcomes
                store successful adaptation episode
                explain context, similarity, gain, cost and confidence
            ELSE IF budget expires:
                mark all tested candidates rejected
                update controller from tested outcome
        IF deployed representation fails two probation windows:
            restore the previous stable version
        update survival scores and prune inactive low-utility features
```

Past labels can rank candidates, but they never serve as their promotion scores. Delayed predictions are attributed to the arena that generated them. No candidate bypasses the safe deployment gate, including a recalled candidate.

The browser records process snapshots at actual engine events and completed labelled windows. These snapshots drive the interactive visualizer and replay; they do not influence adaptation decisions.
