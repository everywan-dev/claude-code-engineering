"""The `second_opinion` probe: ask a *different* model whether a claim still holds.

Invocable as `python3 -m validated_memory.probes.second_opinion`. Implements the
probe contract: read the anchor's envelope as JSON on stdin, answer
`{"verdict": ..., "detail": ...}` as JSON on stdout, exit 0. Every failure mode
is caught here and reported as `unknown` with an explanatory `detail` -- never a
traceback, never a non-zero exit.

======================================================================
WHAT THIS PROBE IS, AND WHAT IT IS NOT
======================================================================
A model reviewing its own output shares its own blind spots, exactly the way a
person does. Asking a *different* model is a genuinely independent check, and
independence is the whole reason the `devils-advocate` agent exists.

But be clear about what comes back:

  🔴 A model's answer is an OPINION, not a measurement.

A `drifted` verdict here means *another model disagrees with what we wrote*. It
is a reason to go and check, not proof that the claim is wrong. A `current`
verdict means *it did not disagree*, which is weaker still.

**This probe must never be the basis for promoting a unit to `measured`.**
`measured` means someone ran something and the output is in the anchor. Nothing
a language model says can create that. If this probe is your only evidence, the
honest state is `hypothesis`.

======================================================================
WHAT IT CAN AND CANNOT CHECK
======================================================================
Suits claims a model can assess from what it knows:

    "The maximum identifier length in this protocol is 63 characters"
    "This configuration key was removed in version 3"

Does *not* suit anything that needs execution or access to your systems. The
other model cannot reach your hosts, read your files, or run your commands. For
those, use a probe that actually runs the check. Asking a model to guess at the
state of a machine it cannot see is how you manufacture confidence out of
nothing -- the same failure mode as folding a network timeout into "still fine".

======================================================================
WHY THE PROMPT WITHHOLDS OUR REASONING
======================================================================
The prompt sends the claim and the criterion. It deliberately does **not** send
how we reached the claim.

Give a model your reasoning and it tends to agree with it. That turns an
independent check into an expensive echo, which is worse than no check at all
because it feels like verification.

======================================================================
CONFIGURATION
======================================================================
    VALIDATED_MEMORY_MODEL_URL   endpoint, OpenAI-compatible chat completions.
                                 Works with any provider that speaks it,
                                 including one you run yourself.
    VALIDATED_MEMORY_MODEL_KEY   bearer token. Omit for a local endpoint that
                                 does not want one.
    VALIDATED_MEMORY_MODEL_NAME  model identifier to ask for.

No key is read from anywhere but the environment, and none is ever written to
the verdict log.

Payload contract (opaque to the framework, interpreted here):

    payload:
      claim: The maximum identifier length is 63 characters
      criterion: Answer about the protocol standard, not any implementation
"""

import json
import os
import sys
import urllib.error
import urllib.request

from .. import verdicts as verdicts_module

TIMEOUT_SECONDS = 45

# Kept short on purpose. A long prompt invites the model to elaborate, and
# what we need is a decision plus its reason.
INSTRUCTIONS = (
    "You are checking whether a written claim still holds.\n"
    "You are given the claim and the criterion to judge it by. You are NOT "
    "given how the claim was reached, deliberately: judge it on its own.\n"
    "Answer with a single JSON object and nothing else:\n"
    '  {"holds": true|false|null, "why": "<one or two sentences>"}\n'
    "Use true if the claim holds, false if it does not, and null if you "
    "cannot tell from what you know.\n"
    "null is a real answer. Prefer it over guessing: a confident wrong answer "
    "here is worse than an honest one."
)


def _unknown(detail):
    return {"verdict": verdicts_module.UNKNOWN, "detail": detail}


def _ask(url, key, model, claim, criterion):
    """Returns (holds, why) or raises. `holds` is True, False or None."""
    body = json.dumps({
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content":
                f"Claim:\n{claim}\n\nCriterion:\n{criterion or 'Judge the claim as written.'}"},
        ],
    }).encode("utf-8")

    request = urllib.request.Request(url, data=body, method="POST")
    request.add_header("Content-Type", "application/json")
    if key:
        request.add_header("Authorization", f"Bearer {key}")

    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        data = json.loads(response.read().decode("utf-8"))

    text = data["choices"][0]["message"]["content"].strip()
    # Some models wrap JSON in a code fence however firmly you ask them not to.
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    verdict = json.loads(text)
    return verdict.get("holds"), (verdict.get("why") or "").strip()


def main():
    try:
        sobre = json.load(sys.stdin)
    except Exception as e:
        print(json.dumps(_unknown(f"envelope could not be read: {e}")))
        return

    carga = sobre.get("payload") or {}
    claim = (carga.get("claim") or "").strip()
    criterion = (carga.get("criterion") or "").strip()
    if not claim:
        print(json.dumps(_unknown(
            "payload has no 'claim'. This probe needs the statement to check, "
            "as text.")))
        return

    url = os.environ.get("VALIDATED_MEMORY_MODEL_URL", "").strip()
    model = os.environ.get("VALIDATED_MEMORY_MODEL_NAME", "").strip()
    key = os.environ.get("VALIDATED_MEMORY_MODEL_KEY", "").strip()
    if not url or not model:
        print(json.dumps(_unknown(
            "no second model configured. Set VALIDATED_MEMORY_MODEL_URL and "
            "VALIDATED_MEMORY_MODEL_NAME. Without them this check cannot run, "
            "and 'could not check' is the honest answer.")))
        return

    try:
        holds, why = _ask(url, key, model, claim, criterion)
    except urllib.error.HTTPError as e:
        print(json.dumps(_unknown(f"the endpoint answered {e.code}")))
        return
    except urllib.error.URLError as e:
        print(json.dumps(_unknown(f"the endpoint could not be reached: {e.reason}")))
        return
    except (KeyError, IndexError, ValueError) as e:
        print(json.dumps(_unknown(
            f"the answer could not be read as a verdict: {e}")))
        return
    except Exception as e:  # a probe never aborts the run
        print(json.dumps(_unknown(f"unexpected failure: {type(e).__name__}: {e}")))
        return

    if holds is True:
        print(json.dumps({
            "verdict": verdicts_module.CURRENT,
            "detail": f"a second model did not disagree ({model}). {why}".strip(),
        }))
    elif holds is False:
        print(json.dumps({
            "verdict": verdicts_module.DRIFTED,
            # Worded as disagreement, not as fact. It is a reason to go and
            # check, not a finding.
            "detail": f"a second model disagrees ({model}), go and check. {why}".strip(),
        }))
    else:
        print(json.dumps(_unknown(
            f"the second model could not tell ({model}). "
            f"{why or 'No reason given.'}")))


if __name__ == "__main__":
    main()
