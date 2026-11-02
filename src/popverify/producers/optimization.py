"""Live optimizer diagnostics adapted from add_numeric_counters.py.

The original trainer patch registered a post-step hook to count real optimizer
calls. This utility supplies the same mechanism without patching external code.
"""

import math

from ..registration import number


class UpdateTracker:
    """Count actual optimizer calls and explicitly declared update attempts.

    Call attempt() immediately before each optimizer.step()/scaler.step(),
    including AMP calls that may be skipped. Call loss() per microbatch and
    targets() before the BCE objective. Use a context manager to remove hooks.
    One tracker is per optimizer/rank; distributed aggregation is external.
    """

    def __init__(self, optimizer):
        self.successful = 0
        self.attempted = 0
        self.nonfinite = 0
        self.losses_observed = 0
        self.target_values = []
        self.target_dtypes = set()
        self.nonfinite_targets = 0
        self.outside_targets = 0
        self._closed = False
        self._hook = optimizer.register_step_post_hook(self._after_step)

    def _active(self):
        if self._closed:
            raise RuntimeError("tracker is closed")

    def _after_step(self, optimizer, positional, keywords):
        self.successful += 1

    def attempt(self):
        self._active()
        self.attempted += 1

    def loss(self, value):
        self._active()
        # Tensor scalar .item() is supported without importing PyTorch here.
        value = value.item() if hasattr(value, "item") else value
        if type(value) not in (int, float):
            raise ValueError("loss must be a numeric scalar")
        self.losses_observed += 1
        if not number(value):
            self.nonfinite += 1

    def targets(self, values, dtype):
        self._active()
        if not isinstance(dtype, str) or not dtype:
            raise ValueError("dtype is required")
        if hasattr(values, "detach"):
            actual_dtype = str(values.dtype).removeprefix("torch.")
            if dtype != actual_dtype:
                raise ValueError("declared target dtype differs from observed tensor dtype")
            values = values.detach().cpu().reshape(-1).tolist()
        values = list(values)
        if not values:
            raise ValueError("empty target observation")
        self.target_dtypes.add(dtype)
        for value in values:
            if type(value) not in (int, float):
                raise ValueError("targets must be numeric")
            if not number(value):
                self.nonfinite_targets += 1
            else:
                self.target_values.append(value)
                self.outside_targets += int(not 0 <= value <= 1)

    def evidence(self):
        """Return version-1-ready records and separate diagnostic coverage.

        Nonfinite targets cannot be represented as JSON numbers; omit their
        target record and preserve explicit diagnostics. A custom assertion or
        scientific review must interpret those diagnostics (no fabricated PASS).
        """
        if self.successful > self.attempted:
            raise ValueError("unrecorded optimizer attempt; counters cannot establish coverage")
        result = {
            "updates": {
                "successful": self.successful,
                "skipped": self.attempted - self.successful,
                "nonfinite": self.nonfinite,
            },
            "diagnostics": {
                "attempted": self.attempted,
                "losses_observed": self.losses_observed,
                "nonfinite_targets": self.nonfinite_targets,
                "outside_unit_targets": self.outside_targets,
                "target_dtypes": sorted(self.target_dtypes),
            },
        }
        if len(self.target_dtypes) == 1 and self.target_values and not self.nonfinite_targets:
            result["targets"] = {
                "dtype": next(iter(self.target_dtypes)),
                "values": self.target_values.copy(),
            }
        return result

    def close(self):
        if not self._closed:
            self._hook.remove()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def parameter_snapshot(model):
    """Export finite trainable tensor values without pickle or checkpoint loads.

    Accepts a PyTorch-style named_parameters() interface. This makes a detached
    CPU copy; cost is proportional to trainable parameters, not a claimed zero
    overhead instrumentation method.
    """
    result = {}
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            values = parameter.detach().cpu().reshape(-1).tolist()
            if any(not number(v) for v in values):
                raise ValueError("nonfinite trainable parameter")
            result[name] = {"shape": list(parameter.shape), "values": values}
    if not result:
        raise ValueError("no trainable parameters")
    return result


def parameter_delta(initial, final):
    """L2 norm on explicitly matching trainable parameter names/shapes."""
    if not initial or initial.keys() != final.keys():
        raise ValueError("trainable parameter identities differ")
    differences = []
    for name, before in initial.items():
        after = final[name]
        if before["shape"] != after["shape"] or len(before["values"]) != len(after["values"]):
            raise ValueError("trainable parameter shape differs")
        for a, b in zip(before["values"], after["values"]):
            if not number(a) or not number(b):
                raise ValueError("nonfinite parameter value")
            differences.append(b - a)
    # math.hypot avoids overflow from squaring large finite values.
    delta = math.hypot(*differences)
    if not number(delta):
        raise ValueError("nonfinite parameter delta")
    return delta
