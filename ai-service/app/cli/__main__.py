from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from app.core.config import settings
from app.pipeline.validator import PipelineValidator


def cmd_info(args: argparse.Namespace) -> int:
    """Print service metadata, versions, and paths."""
    print("=" * 65)
    print("ReleaseGuard AI Service — Environment & Version Summary")
    print("=" * 65)
    print(f"Service Version   : {settings.SERVICE_VERSION}")
    print(f"Model Version     : {settings.MODEL_VERSION}")
    print(f"Feature Version   : {settings.FEATURE_VERSION}")
    print(f"Dataset Version   : {settings.DATASET_VERSION}")
    print(f"Server Host:Port  : {settings.HOST}:{settings.PORT}")
    print()
    print("Paths:")
    print(f"  Root Dir        : {settings.ROOT_DIR}")
    print(f"  Artifacts Dir   : {settings.ARTIFACTS_DIR}")
    print(f"  Data Dir        : {settings.DATA_DIR}")
    print(f"  Model Artifact  : {settings.production_model_path}")
    print(f"    -> Exists     : {settings.production_model_path.exists()}")
    print(f"  Model Metadata  : {settings.production_metadata_path}")
    print(f"    -> Exists     : {settings.production_metadata_path.exists()}")
    print("=" * 65)
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the FastAPI application using uvicorn."""
    import uvicorn

    host = args.host or settings.HOST
    port = args.port or settings.PORT
    reload = args.reload

    print(f"Starting ReleaseGuard AI Service on http://{host}:{port} (reload={reload})...")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
    return 0


def cmd_pipeline_validate(args: argparse.Namespace) -> int:
    """Run pre-flight checks on all dataset and model stages."""
    v = args.version or settings.MODEL_VERSION
    validator = PipelineValidator()
    results = validator.validate_all(model_version=v)

    print("=" * 70)
    print(f"ReleaseGuard Pipeline Validation Report (Model v{v})")
    print("=" * 70)
    all_ok = True

    for stage, res in results.items():
        status_sym = "[OK]" if res.is_valid else "[FAIL]"
        if not res.is_valid:
            all_ok = False
        print(f"  {status_sym} {stage.replace('_', ' ').title():<22} (v{res.version})")
        if res.errors:
            for err in res.errors:
                print(f"         ! {err}")

    ready_train, train_errs = validator.is_ready_for_training()
    ready_promote, promote_errs = validator.is_ready_for_promotion(v)

    print("-" * 70)
    print(f"  Ready for Training  : {'YES' if ready_train else 'NO'}")
    print(f"  Ready for Promotion : {'YES' if ready_promote else 'NO'}")
    print("=" * 70)

    return 0 if all_ok else 1


def cmd_pipeline_collect(args: argparse.Namespace) -> int:
    from app.pipeline.collection import collect_prs

    collect_prs(limit=args.limit)
    return 0


def cmd_pipeline_dataset(args: argparse.Namespace) -> int:
    from app.pipeline.dataset import run_dataset_pipeline

    run_dataset_pipeline(split=args.split, freeze=args.freeze)
    return 0


def cmd_pipeline_train(args: argparse.Namespace) -> int:
    from app.pipeline.training import train_models

    v = args.version or settings.MODEL_VERSION
    train_models(v)
    return 0


def cmd_pipeline_evaluate(args: argparse.Namespace) -> int:
    from app.pipeline.evaluation import evaluate_models

    v = args.version or settings.MODEL_VERSION
    evaluate_models(v)
    return 0


def cmd_pipeline_promote(args: argparse.Namespace) -> int:
    from app.pipeline.promotion import promote_model

    v = args.version or settings.MODEL_VERSION
    promote_model(v)
    return 0


def cmd_pipeline_run_all(args: argparse.Namespace) -> int:
    from app.pipeline.runner import run_pipeline

    v = args.version or settings.MODEL_VERSION
    run_pipeline(version=v, skip_dataset=args.skip_dataset)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="releaseguard-ai",
        description="ReleaseGuard AI Service CLI & Pipeline Orchestrator",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: info
    subparsers.add_parser("info", help="Display environment, active versions, and paths")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Run the FastAPI prediction server")
    serve_parser.add_argument("--host", default=None, help=f"Bind host (default: {settings.HOST})")
    serve_parser.add_argument("--port", type=int, default=None, help=f"Bind port (default: {settings.PORT})")
    serve_parser.add_argument("--reload", action="store_true", help="Enable hot reload")

    # Command: pipeline
    pipe_parser = subparsers.add_parser("pipeline", help="Manage data collection, training, and promotion")
    pipe_sub = pipe_parser.add_subparsers(dest="pipeline_action", help="Pipeline action")

    # pipeline validate
    val_p = pipe_sub.add_parser("validate", help="Validate dataset, models, and artifacts")
    val_p.add_argument("--version", default=None, help="Model version to validate (default: 2.0.0)")

    # pipeline collect
    col_p = pipe_sub.add_parser("collect", help="Collect PRs and defect signals")
    col_p.add_argument("--limit", type=int, default=None, help="Limit number of PRs")

    # pipeline dataset
    ds_p = pipe_sub.add_parser("dataset", help="Build labels, features, splits, and freeze dataset")
    ds_p.add_argument("--no-split", dest="split", action="store_false", default=True, help="Skip dataset split")
    ds_p.add_argument("--no-freeze", dest="freeze", action="store_false", default=True, help="Skip dataset freeze")

    # pipeline train
    tr_p = pipe_sub.add_parser("train", help="Train baseline and XGBoost models")
    tr_p.add_argument("--version", default=None, help="Target model version (default: 2.0.0)")

    # pipeline evaluate
    ev_p = pipe_sub.add_parser("evaluate", help="Evaluate models on test split")
    ev_p.add_argument("--version", default=None, help="Target model version (default: 2.0.0)")

    # pipeline promote
    pr_p = pipe_sub.add_parser("promote", help="Promote candidate model to production artifact")
    pr_p.add_argument("--version", default=None, help="Target model version (default: 2.0.0)")

    # pipeline run-all
    all_p = pipe_sub.add_parser("run-all", help="Execute complete pipeline (train -> eval -> promote)")
    all_p.add_argument("--version", default=None, help="Target model version (default: 2.0.0)")
    all_p.add_argument(
        "--build-dataset",
        dest="skip_dataset",
        action="store_false",
        default=True,
        help="Rebuild labels and features before training (default: uses existing frozen splits)",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "info":
        return cmd_info(args)
    elif args.command == "serve":
        return cmd_serve(args)
    elif args.command == "pipeline":
        if not args.pipeline_action:
            print("Please specify a pipeline action: validate, collect, dataset, train, evaluate, promote, run-all")
            return 1
        actions = {
            "validate": cmd_pipeline_validate,
            "collect": cmd_pipeline_collect,
            "dataset": cmd_pipeline_dataset,
            "train": cmd_pipeline_train,
            "evaluate": cmd_pipeline_evaluate,
            "promote": cmd_pipeline_promote,
            "run-all": cmd_pipeline_run_all,
        }
        action_fn = actions.get(args.pipeline_action)
        if action_fn:
            return action_fn(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
