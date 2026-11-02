"""Actual CPU PyTorch tests; optional environment, reported explicitly if absent."""

import importlib.util
import unittest

TORCH = importlib.util.find_spec("torch") is not None


@unittest.skipUnless(TORCH, "PyTorch optional integration environment not installed")
class TorchProducerTests(unittest.TestCase):
    def test_live_steps_parameter_changes_and_frozen_parameters(self):
        import torch
        from popverify.producers.optimization import (
            UpdateTracker,
            parameter_delta,
            parameter_snapshot,
        )

        model = torch.nn.Linear(2, 1)
        model.bias.requires_grad_(False)
        before = parameter_snapshot(model)
        self.assertNotIn("bias", before)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
        with UpdateTracker(optimizer) as tracker:
            y = torch.tensor([0.0, 1.0])
            tracker.targets(y, "float32")
            loss = torch.nn.functional.binary_cross_entropy_with_logits(
                model(torch.tensor([[0.0, 0.0], [1.0, 1.0]])).reshape(-1), y
            )
            tracker.loss(loss)
            loss.backward()
            tracker.attempt()
            optimizer.step()
            tracker.attempt()  # deliberate no-call boundary
            observed = tracker.evidence()
        self.assertEqual(observed["updates"], {"successful": 1, "skipped": 1, "nonfinite": 0})
        self.assertGreater(parameter_delta(before, parameter_snapshot(model)), 0)

    def test_gradscaler_cpu_skip_is_not_counted_as_success(self):
        import torch
        from popverify.producers.optimization import UpdateTracker

        model = torch.nn.Linear(1, 1)
        optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
        scaler = torch.amp.GradScaler("cpu")
        with UpdateTracker(optimizer) as tracker:
            for factor in [1.0, float("inf")]:
                optimizer.zero_grad()
                loss = model(torch.ones(1, 1)).sum() * factor
                tracker.loss(loss)
                scaler.scale(loss).backward()
                tracker.attempt()
                scaler.step(optimizer)
                scaler.update()
            observed = tracker.evidence()["updates"]
        self.assertEqual(observed, {"successful": 1, "skipped": 1, "nonfinite": 1})


if __name__ == "__main__":
    unittest.main()
