"""
CLI Runner for LunarVision Real-Data Benchmark (Phase 1)
Supports:
python -m backend.scripts.run_benchmark --manifest m.csv --strategy standard|normalized|crater|auto --norm-mode flatten|gradient|relight|all --out results/
"""

import sys
import argparse
import logging
from pathlib import Path

# Ensure root workspace is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend import config
from backend.services.benchmark import BenchmarkService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_benchmark")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run LunarVision Real-Data Benchmark Suite (Phase 1)"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to manifest CSV (pair_id, source_path, reference_path, [ground_truth_path])"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default=config.DEFAULT_BENCHMARK_STRATEGY,
        choices=["standard", "normalized", "crater", "auto"],
        help="Registration strategy to evaluate (Only 'standard' is supported in Phase 1)"
    )
    parser.add_argument(
        "--norm-mode",
        type=str,
        default=config.DEFAULT_BENCHMARK_NORM_MODE,
        choices=["flatten", "gradient", "relight", "all"],
        help="Illumination normalization mode for normalized strategy"
    )
    parser.add_argument(
        "--out",
        type=str,
        default=config.DEFAULT_BENCHMARK_OUTPUT_DIR,
        help="Output directory to save results.csv, summary.json, and summary.md"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=config.DEFAULT_RANDOM_SEED,
        help="Random seed for reproducible benchmark execution"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Guard: Non-standard strategies are NOT yet implemented in Phase 1
    if args.strategy != "standard":
        logger.error(
            f"Strategy '{args.strategy}' is not yet implemented. "
            f"Per Phase 1 specification, only the 'standard' strategy is supported. "
            f"Strategies 'normalized', 'crater', and 'auto' belong to later phases."
        )
        print(
            f"ERROR: Strategy '{args.strategy}' is not implemented in Phase 1. "
            f"Use '--strategy standard'.",
            file=sys.stderr
        )
        sys.exit(1)

    logger.info("Initializing LunarVision Benchmark Suite (Phase 1)...")
    logger.info(f"Manifest: {args.manifest}")
    logger.info(f"Strategy: {args.strategy}")
    logger.info(f"Output Directory: {args.out}")
    logger.info(f"Random Seed: {args.seed}")

    benchmark_svc = BenchmarkService(seed=args.seed)

    try:
        summary = benchmark_svc.run_benchmark(
            manifest_path=args.manifest,
            output_dir=args.out,
            strategy=args.strategy,
            norm_mode=args.norm_mode
        )
    except Exception as e:
        logger.error(f"Benchmark execution failed: {e}")
        sys.exit(1)

    out_path = Path(args.out)
    print("\n" + "=" * 60)
    print("  LUNARVISION BENCHMARK EXECUTION COMPLETE (PHASE 1)")
    print("=" * 60)
    print(f"Total Pairs Evaluated : {summary.get('total_pairs')}")
    print(f"Successful Pairs      : {summary.get('successful_pairs')} ({summary.get('success_rate', 0.0) * 100:.1f}%)")
    print(f"Failed Pairs          : {summary.get('failed_pairs')}")
    if summary.get("mean_ground_truth_error") is not None:
        print(f"Mean GT Pixel Error   : {summary.get('mean_ground_truth_error')} px")
    print(f"Median Runtime        : {summary.get('median_runtime_ms')} ms")
    print("-" * 60)
    print(f"Results CSV           : {out_path / 'results.csv'}")
    print(f"Summary JSON          : {out_path / 'summary.json'}")
    print(f"Summary Markdown      : {out_path / 'summary.md'}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
