# Decisions

1. Evaluate every registered assertion.
2. If any assertion is contradicted by usable evidence, return FAIL.
3. Otherwise, if any assertion lacks sufficient usable evidence, return UNRESOLVED.
4. Otherwise return PASS.

FAIL takes priority over missing evidence. A missing completion record is UNRESOLVED; an explicit false completion record contradicts the requirement and is FAIL. A finite target outside [0,1] is FAIL; a malformed target record is UNRESOLVED. A digest mismatch is FAIL; an inaccessible artifact is UNRESOLVED. Bundled changes leave single-factor attribution unresolved when that optional assertion is registered.

An empty assertion set or one missing mandatory gate/both-arm coverage is an invalid registration, not PASS. Scientific review is still necessary: requirements can be insufficient, logs untruthful or an analysis selected retrospectively. No statistical independence, model ranking or truth guarantee follows from receipt acceptance.
