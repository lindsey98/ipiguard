from dotenv import load_dotenv
from typing import Any, Optional, Union, List
import argparse
import json
import os
import time
from cohere.core.api_error import ApiError
from google.api_core.exceptions import InternalServerError
from openai import BadRequestError

from agentdojo.logging import Logger, TraceLogger
from agentdojo.task_suite.task_suite import TaskSuite
from agentdojo.agent_pipeline.agent_pipeline import DEFENSES, AgentPipeline, PipelineConfig
from agentdojo.attacks.attack_registry import ATTACKS, load_attack
from agentdojo.benchmark import SuiteResults, benchmark_suite_with_injections, benchmark_suite_without_injections
from agentdojo.logging import OutputLogger
from agentdojo.models import ModelsEnum
from agentdojo.task_suite.load_suites import get_suite, get_suites
from agentdojo.task_suite.task_suite import TaskSuite
from agentdojo.agent_pipeline.llms.ipiguard_llm import MalformedModelOutputError
from agentdojo.functions_runtime import FunctionCall
from data_module import AGENTDOJO_SUITES, AGENTDYN_SUITES, initialize_dataset
from tqdm import tqdm
# Per-task logging is handled by AgentDojo's TraceLogger (see benign_eval/eval).

class AgentTask:

    @staticmethod
    def benign_run(agent_pipeline, suite, user_task):
        messages = []
        args = {"input_tokens": 0, "output_tokens": 0}
        try:
            utility, security, messages, args = suite.run_task_with_pipeline_msg(
                agent_pipeline, user_task, injection_task=None, injections={}, extra_args={"input_tokens": 0, "output_tokens": 0}
            )
        except BadRequestError as e:
            if e.code == "context_length_exceeded" or e.param == "max_tokens":
                print(
                    f"Skipping task '{user_task.ID}' due to context_length_exceeded: {e}"
                )
                utility = False
                security = True
            else:
                raise e
        except ApiError as e:
            if "internal server error" in str(e):
                print(
                    f"Skipping task '{user_task.ID}' because of internal server error: {e}"
                )
                utility = False
                security = True
            else:
                raise e
        except InternalServerError as e:
                    print(
                        f"Skipping task '{user_task.ID}' because of internal server error: {e}"
                    )
                    utility = False
                    security = True
        except MalformedModelOutputError as e:
            print(f"Skipping task '{user_task.ID}' because of malformed model output: {e}")
            utility = False
            security = True

        return 1 - int(security), int(utility), messages, args

    @staticmethod
    def run(agent_pipeline, suite, attacks, user_task, injection_task, extra_args, security_check_fn=None):
        inj_id = injection_task.ID if injection_task is not None else "data_injection"
        try:
            utility, security, messages, args = suite.run_task_with_pipeline_msg(
                agent_pipeline, user_task, injection_task, attacks,
                extra_args={"input_tokens": 0, "output_tokens": 0}, security_check_fn=security_check_fn,
            )
        except BadRequestError as e:
            if e.code == "context_length_exceeded" or e.param == "max_tokens":
                print(
                    f"Skipping task '{user_task.ID}' with '{inj_id}' due to context_length_exceeded: {e}"
                )
                utility = False
                security = True
                messages = []
                args = {"input_tokens": 0, "output_tokens": 0}
            else:
                utility = False
                security = True
                messages = []
                args = {"input_tokens": 0, "output_tokens": 0}
        except ApiError as e:
            if "internal server error" in str(e):
                print(
                    f"Skipping task '{user_task.ID}' with '{inj_id}' because of internal server error: {e}"
                )
                utility = False
                security = True
                messages = []
                args = {"input_tokens": 0, "output_tokens": 0}
            else:
                raise e
        except InternalServerError as e:
                    print(
                        f"Skipping task '{user_task.ID}' with '{inj_id}' because of internal server error: {e}"
                    )
                    utility = False
                    security = True
                    messages = []
                    args = {"input_tokens": 0, "output_tokens": 0}
        except MalformedModelOutputError as e:
            print(
                f"Skipping task '{user_task.ID}' with '{inj_id}' because of malformed model output: {e}"
            )
            utility = False
            security = True
            messages = []
            args = {"input_tokens": 0, "output_tokens": 0}

        return int(security), int(utility), messages, args

def parse_args():
    """Command-line interface.

    With attack:
        python main.py MODEL --run-attack --attack important_instructions \\
            --suites banking slack travel workspace --defense ipiguard
    Without attack (benign):
        python main.py MODEL --suites banking slack travel workspace --defense ipiguard

    MODEL is positional (e.g. Qwen3.6-35B-A3B, or local:Qwen3.6-35B-A3B, gpt-4o-mini-...).
    Output always goes under logs/ unless --output_dir is given.
    """
    p = argparse.ArgumentParser(description="Run the IPIGuard / AgentDojo evaluation.")
    p.add_argument("agent_model", help="agent model, e.g. Qwen3.6-35B-A3B or local:Qwen3.6-35B-A3B")
    p.add_argument("--run-attack", dest="run_attack", action="store_true",
                   help="run under attack (omit for the benign, no-attack run)")
    p.add_argument("--attack", dest="attack_name", default="important_instructions",
                   help="attack name (only used with --run-attack), e.g. important_instructions")
    p.add_argument("--suites", dest="suite_name", nargs="+",
                   default=["banking", "slack", "travel", "workspace"],
                   help="suites to run: banking slack travel workspace shopping github dailylife, "
                        "or a group: all / agentdyn / everything")
    p.add_argument("--defense", dest="defense_name", default="ipiguard",
                   help="defense: None (original model) or ipiguard")
    p.add_argument("--output_dir", dest="output_dir", default="logs/",
                   help="output directory (default logs/)")
    p.add_argument("--benchmark-version", dest="benchmark_version", default="v1.2",
                   help="benchmark suite version (default v1.2)")
    p.add_argument("-ut", "--user-task", dest="user_tasks", action="append", default=None,
                   help="user task(s) to run, repeatable (e.g. -ut 0 -ut 3 or -ut user_task_0). "
                        "If omitted, all user tasks in the suite are run.")
    p.add_argument("-it", "--injection-task", dest="injection_tasks", action="append", default=None,
                   help="injection task(s) to run, repeatable (e.g. -it 1 or -it injection_task_1). "
                        "If omitted, all injection tasks in the suite are run.")
    p.add_argument("--force-rerun", dest="force_rerun", action="store_true",
                   help="rerun tasks even if a completed trace JSON already exists")
    p.add_argument("--html", action="store_true",
                   help="also write a rendered .html next to each .json trace")
    args = p.parse_args()
    args.mode = "under_attack" if args.run_attack else "benign"
    args.user_tasks = tuple(args.user_tasks or ())
    args.injection_tasks = tuple(args.injection_tasks or ())
    return args


def _id_selected(selected: tuple, current_int: int, prefix: str) -> bool:
    """True if current task id passes the debug filter (empty selection = run all).

    Accepts both bare ids ("3") and full ids ("user_task_3" / "injection_task_3").
    """
    if not selected:
        return True
    norm = {str(s).replace(prefix, "") for s in selected}
    return str(current_int) in norm


def _cached_result(script_args, pipeline_name, suite_name, user_task_id, attack_type, injection_task_id):
    """Return (task_reward, utility) from an existing trace JSON, or None to (re)run.

    Reuses results only when the file is complete (has utility/security and no
    recorded error), so interrupted or crashed tasks are rerun.
    """
    if script_args.force_rerun:
        return None
    path = os.path.join(
        script_args.output_dir,
        pipeline_name.replace("/", "_"),
        suite_name,
        user_task_id,
        attack_type,
        f"{injection_task_id or 'none'}.json",
    )
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("error") is not None or "security" not in data or "utility" not in data:
        return None
    return int(bool(data["security"])), int(bool(data["utility"]))


def _log_run_context(logger, args):
    """Record IPIGuard DAG snapshots + token usage into the trace JSON (when present).

    For non-IPIGuard runs these keys are simply absent and nothing extra is logged.
    """
    for key in ("pre_plan", "initial_dag", "expanded_dag", "dag_events", "runtime_new_tool_calls", "input_tokens", "output_tokens"):
        if key in args and args[key] is not None:
            log_key = "new_tool_calls" if key == "runtime_new_tool_calls" else key
            logger.set_contextarg(log_key, args[key])


def benign_eval(script_args, agent_pipeline, suite, agent_test_dataset, pipeline_name):
    sum = 0
    security = 0
    useful = 0
    for user_task_id in tqdm(agent_test_dataset, desc="Evaluating on the test dataset"):
        # --user-task is a debugging filter: when unset, run every user task.
        if not _id_selected(script_args.user_tasks, user_task_id, "user_task_"):
            continue
        user_task_to_run = suite.get_user_task_by_id(f"user_task_{user_task_id}")

        cached = _cached_result(script_args, pipeline_name, suite.name, user_task_to_run.ID, "none", None)
        if cached is not None:
            task_reward, utility = cached
            sum += 1
            security += task_reward
            useful += utility
            continue

        # AgentDojo-style logging: one JSON per task at
        #   {logdir}/{pipeline_name}/{suite}/{user_task_id}/none/none.json
        with TraceLogger(
            delegate=Logger.get(),
            suite_name=suite.name,
            user_task_id=user_task_to_run.ID,
            injection_task_id=None,
            injections={},
            attack_type="none",
            pipeline_name=pipeline_name,
        ) as logger:
            task_reward, utility, messages, args = AgentTask.benign_run(
                agent_pipeline, suite, user_task_to_run)
            logger.set_contextarg("utility", bool(utility))
            logger.set_contextarg("security", bool(task_reward))
            _log_run_context(logger, args)

        sum += 1
        security += task_reward
        useful += utility

    if sum == 0:
        raise ValueError(
            f"No tasks matched in suite '{suite.name}' (user_tasks={script_args.user_tasks}); "
            "check the --user-task/-ut debug filter."
        )
    asr = security * 100 / sum
    ability = useful * 100 / sum

    return security, useful, sum, asr, ability



def _data_only_eval(script_args, agent_pipeline, suite, attacker, agent_test_dataset, pipeline_name):
    """Evaluate a data-only attack (e.g. data_only_syntactic).

    Data-only attacks don't inject via `attacker.attack()` (that returns {}). Instead the injected
    data + per-case security check live on each user task as INJECTED_DATA_<SUB> / SECURITY_CHECKS_<SUB>.
    Each INJECTED_DATA entry is one test case (injection_task_<idx>): inject it into the environment and
    score with SECURITY_CHECKS_<SUB>[idx] (True = the injected data leaked = attack succeeded).
    """
    subcategory = attacker.subcategory
    data_field = f"INJECTED_DATA_{subcategory}"
    checks_field = f"SECURITY_CHECKS_{subcategory}"
    user_task_ids = sorted({u for (u, _) in agent_test_dataset})

    sum = security = useful = 0
    for user_task_id in tqdm(user_task_ids, desc="Evaluating on the test dataset"):
        if not _id_selected(script_args.user_tasks, user_task_id, "user_task_"):
            continue
        user_task = suite.get_user_task_by_id(f"user_task_{user_task_id}")
        injected_list = getattr(user_task, data_field, None)
        checks_list = getattr(user_task, checks_field, None)
        if not injected_list or not checks_list:
            print(f"Skipping {user_task.ID}: no {data_field}/{checks_field} (task not part of this data-only attack)")
            continue

        for idx, injected_data in enumerate(injected_list):
            if not _id_selected(script_args.injection_tasks, idx, "injection_task_"):
                continue
            injection_task_id = f"injection_task_{idx}"
            security_check_fn = checks_list[idx]

            cached = _cached_result(
                script_args, pipeline_name, suite.name, user_task.ID, script_args.attack_name, injection_task_id
            )
            if cached is not None:
                task_reward, utility = cached
                sum += 1
                security += task_reward
                useful += utility
                continue

            with TraceLogger(
                delegate=Logger.get(),
                suite_name=suite.name,
                user_task_id=user_task.ID,
                injection_task_id=injection_task_id,
                injections=injected_data,
                attack_type=script_args.attack_name,
                pipeline_name=pipeline_name,
            ) as logger:
                task_reward, utility, history, args = AgentTask.run(
                    agent_pipeline, suite, injected_data, user_task, None, extra_args={},
                    security_check_fn=security_check_fn,
                )
                logger.set_contextarg("utility", bool(utility))
                logger.set_contextarg("security", bool(task_reward))
                _log_run_context(logger, args)

            sum += 1
            security += task_reward
            useful += utility

    if sum == 0:
        raise ValueError(
            f"No data-only cases matched in suite '{suite.name}' — no user task defines "
            f"{data_field}/{checks_field} (or all were filtered out)."
        )
    asr = security * 100 / sum
    ability = useful * 100 / sum
    return security, useful, sum, asr, ability


def eval(script_args, agent_pipeline, suite, attacker, agent_test_dataset, pipeline_name):
    # Data-only attacks (attacker.attack() returns {}) use a separate injection + scoring path.
    if getattr(attacker, "is_data_injection", False):
        return _data_only_eval(script_args, agent_pipeline, suite, attacker, agent_test_dataset, pipeline_name)

    sum = 0
    security = 0
    useful = 0

    for user_task_id, injection_task_id in tqdm(agent_test_dataset, desc="Evaluating on the test dataset"):
        # --user-task / --injection-task are debugging filters: when unset, run every pair.
        if not _id_selected(script_args.user_tasks, user_task_id, "user_task_"):
            continue
        if not _id_selected(script_args.injection_tasks, injection_task_id, "injection_task_"):
            continue

        user_task_to_run = suite.get_user_task_by_id(f"user_task_{user_task_id}")
        injection_task_to_run = suite.get_injection_task_by_id(f"injection_task_{injection_task_id}")

        cached = _cached_result(
            script_args, pipeline_name, suite.name, user_task_to_run.ID,
            script_args.attack_name, injection_task_to_run.ID,
        )
        if cached is not None:
            task_reward, utility = cached
            sum += 1
            security += task_reward
            useful += utility
            continue

        attacks = attacker.attack(user_task_to_run, injection_task_to_run)

        # AgentDojo-style logging: one JSON per (task, injection) at
        #   {logdir}/{pipeline_name}/{suite}/{user_task_id}/{attack_name}/{injection_task_id}.json
        with TraceLogger(
            delegate=Logger.get(),
            suite_name=suite.name,
            user_task_id=user_task_to_run.ID,
            injection_task_id=injection_task_to_run.ID,
            injections=attacks,
            attack_type=script_args.attack_name,
            pipeline_name=pipeline_name,
        ) as logger:
            task_reward, utility, history, args = AgentTask.run(
                agent_pipeline, suite, attacks, user_task_to_run, injection_task_to_run, extra_args={})
            logger.set_contextarg("utility", bool(utility))
            logger.set_contextarg("security", bool(task_reward))
            _log_run_context(logger, args)

        sum += 1
        security += task_reward
        useful += utility

    if sum == 0:
        raise ValueError(
            f"No (task, injection) pairs matched in suite '{suite.name}' (user_tasks={script_args.user_tasks}, injection_tasks={script_args.injection_tasks}); "
            "check the --uid/--iid debug filters."
        )
    asr = security * 100 / sum
    ability = useful * 100 / sum

    return security, useful, sum, asr, ability

if __name__ == '__main__':
    load_dotenv()
    script_args = parse_args()

    # opt-in HTML trace rendering (TraceLogger.save reads this env var)
    if script_args.html:
        os.environ["AGENTDOJO_TRACE_HTML"] = "1"

    # Pipeline name == top-level log directory, AgentDojo style:
    #   {output_dir}/{pipeline_name}/{suite}/{user_task}/{attack_type}/{injection}.json
    pipeline_name = script_args.agent_model.replace("/", "_").split(":")[-1]
    if script_args.defense_name != "None":
        pipeline_name = f"{pipeline_name}+{script_args.defense_name}"

    logdir = script_args.output_dir
    os.makedirs(logdir, exist_ok=True)

    if len(script_args.suite_name) == 1:
        if script_args.suite_name[0] == "all":
            script_args.suite_name = AGENTDOJO_SUITES
        elif script_args.suite_name[0] == "agentdyn":
            script_args.suite_name = AGENTDYN_SUITES
        elif script_args.suite_name[0] == "everything":
            script_args.suite_name = AGENTDOJO_SUITES + AGENTDYN_SUITES

    success = 0
    attack = 0
    all = 0
    # OutputLogger sets the log root (TraceLogger writes its tree under logdir)
    # and mirrors each task's trace to the console.
    with OutputLogger(logdir=logdir):
        for suite_n in tqdm(script_args.suite_name):
            suite = get_suite(script_args.benchmark_version, suite_n)
            # accept an optional "provider:" prefix (e.g. "local:Qwen3.6-35B-A3B")
            model = ModelsEnum(script_args.agent_model.split(":")[-1])

            # Initialization
            if script_args.defense_name == "None":
                pipeline = AgentPipeline.from_config(
                    PipelineConfig(
                        llm=model, defense=None, system_message_name=None, system_message=None
                    )
                )
            else:
                pipeline = AgentPipeline.from_config(
                    PipelineConfig(
                        llm=model, defense=script_args.defense_name, system_message_name=None, system_message=None
                    )
                )

            if script_args.mode == "benign":
                dataset = initialize_dataset(suite_n, benign=True, benchmark_version=script_args.benchmark_version)
                security, useful, sum, suite_asr, ability = benign_eval(
                    script_args, pipeline, suite, dataset, pipeline_name)
            elif script_args.mode == "under_attack":
                attacker = load_attack(script_args.attack_name, suite, pipeline)
                dataset = initialize_dataset(suite_n, benchmark_version=script_args.benchmark_version)
                security, useful, sum, suite_asr, ability = eval(
                    script_args, pipeline, suite, attacker, dataset, pipeline_name)
            else:
                raise ValueError(f"Unknown mode: {script_args.mode}")

            success += useful
            attack += security
            all += sum
            print(f"Suite: {suite_n}, ASR: {suite_asr} %, Utility: {ability} %")
            abi = success * 100 / all
            asr = attack * 100 / all
            print(f"Overall ASR: {asr} %, Overall Utility: {abi} %")