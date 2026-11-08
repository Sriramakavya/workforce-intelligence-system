"""Convenience entry point for the full workforce intelligence workflow."""
import argparse
from src.pipeline import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate, validate and analyse workforce data")
    parser.add_argument("--scale", choices=["starter", "full"], default="starter")
    parser.add_argument("--seed", type=int, default=20261022)
    args = parser.parse_args()
    run(args.scale, args.seed)
